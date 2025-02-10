import tkinter as tk
import appdirs, os, json, subprocess, re

HOME_CONFIG_DIRECTORY = appdirs.user_config_dir(appname='tracemap')
DEFAULT_COLORS = {
	"BG_COLOR": "#000000",
	"FG_COLOR": "#00ff00",
	"FG_DARK": "#119911",
	"COUNTRY_OUTLINE": "#000000",
	"COUNTRY_FILL": "#085511",
	"COUNTRY_HIGHLIGHT": "#007700",
	"CONNECTION_START": "#00ffcc",
	"CONNECTION_END": "#00ff55"
}
ROBINSON_PROJECTION_TABLE = [1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427, 0.9216, 0.8962, 0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322]

color_config = ""
try:
	with open(f"{HOME_CONFIG_DIRECTORY}/colors.conf", "r", encoding="utf-8") as f:
		color_config = f.read()
except:
	for k, v in DEFAULT_COLORS.items():
		color_config += f"{k}: {v}\n"
	try:
		try:
			os.mkdir(HOME_CONFIG_DIRECTORY)
		except:
			pass
		with open(f"{HOME_CONFIG_DIRECTORY}/colors.conf", "w", encoding="utf-8") as f:
			f.write(color_config)
	except Exception as e:
		print(f"Failed to create config file: {e}")

try:
	for line in color_config.replace(" ", "").split("\n"):
		try:
			globals()[line.split(":")[0]] = line.split(":")[1]
		except:
			pass
except Exception as e:
	print(f"Failed to parse config file: {e}")

for k, v in DEFAULT_COLORS.items():
	if k not in globals():
		print(f'Color "{k}" not found in config file')
		globals()[k] = v
		try:
			with open(f"{HOME_CONFIG_DIRECTORY}/colors.conf", "a", encoding="utf-8") as f:
				f.write(f"{k}: {v}\n")
				print(f"Added line to config file ({k}: {v})")
		except Exception as e:
			print(f"Failed to add color {k} to config file: {e}")
		
CONNECTION_START_RGB = (
	int(CONNECTION_START[1:3], 16),
	int(CONNECTION_START[3:5], 16),
	int(CONNECTION_START[5:7], 16)
)
CONNECTION_END_RGB = (
	int(CONNECTION_END[1:3], 16),
	int(CONNECTION_END[3:5], 16),
	int(CONNECTION_END[5:7], 16)
)
CONNECTION_DIFF_RGB = [CONNECTION_END_RGB[i] - CONNECTION_START_RGB[i] for i in range(len(CONNECTION_END_RGB))]

MAP_WIDTH = 1000
MAP_HEIGHT = 507
raw_map_svg = {}
try:
	with open(f"map-svg.json", "r", encoding="utf-8") as f:
		raw_map_svg = json.load(f)
except Exception as e:
	print(f"Failed to parse map file: {e}")

map_svg = {}
for country, outline in raw_map_svg.items():
	map_svg[country] = []
	for line in outline[1:].split("M"):
		points = []
		for segment in line.split("L"):
			segmentXY = segment.split(",")
			points.append(float(segmentXY[0]))
			points.append(float(segmentXY[1]))
		map_svg[country].append(points)



root = tk.Tk()
root.title("TraceMap")
root.geometry("1100x500")
root.configure(bg=BG_COLOR)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

canvas = tk.Canvas(root, bg=BG_COLOR, highlightbackground=FG_DARK)
canvas.grid(sticky="NSEW", rowspan=2)

canvas_countries = {}
highlighted_countries = {}
canvas_points = []
canvas_arrows = []
canvas_point_ids = []
canvas_arrow_ids = []
current_redraw_map_instance = []
def redraw_map(event):
	map_stretch_x = canvas.winfo_width() / MAP_WIDTH
	map_stretch_y = canvas.winfo_height() / MAP_HEIGHT
	current_redraw_map_instance = [map_stretch_x, map_stretch_y]
	canvas.delete("all")
	canvas_point_ids = []
	canvas_arrow_ids = []
	for country, outline in map_svg.items():
		country_polygons = []
		for line in outline:
			nums = line.copy()
			for i in range(0, len(nums), 2):
				nums[i] *= map_stretch_x
				nums[i+1] *= map_stretch_y
			
			if current_redraw_map_instance != [map_stretch_x, map_stretch_y]:
				return
			
			color = COUNTRY_FILL
			if country in highlighted_countries:
				color = highlighted_countries[country]

			country_polygons.append(canvas.create_polygon(*nums, outline=COUNTRY_OUTLINE, fill=color, width=1))

		canvas_countries[country] = country_polygons

	for x, y in canvas_points:
		redraw_point(x, y)
	for i in range(len(canvas_arrows)):
		interpolation = i/max(len(canvas_arrows)-1, 1)
		color_rgb = [int(CONNECTION_START_RGB[j] + interpolation*CONNECTION_DIFF_RGB[j]) for j in range(3)]
		color = "#"
		for j in range(3):
			component = hex(color_rgb[j])[2:]
			if len(component) < 2:
				component = "0" + component
			color += component
		redraw_arrow(canvas_arrows[i], color)

root.bind("<Configure>", redraw_map)

def draw_point(x, y):
	canvas_points.append((x, y))
	redraw_point(x, y)
def redraw_point(x, y):
	x *= canvas.winfo_width()
	y *= canvas.winfo_height()
	canvas_point_ids.append(canvas.create_oval(x-3, y-3, x+3, y+3, fill=FG_COLOR))

def draw_arrow(lon1, lat1, lon2, lat2):
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	resolution = int(abs(dlat) / 10)+1
	points = []
	for i in range(resolution):
		x, y = robinson_projection(lon1 + dlon*(i/resolution), lat1 + dlat*(i/resolution))
		points.append((x, y))
	x, y = robinson_projection(lon2, lat2)
	points.append((x, y))

	canvas_arrows.append(points)
	
	redraw_arrow(points, CONNECTION_START)
def redraw_arrow(arrow, color):
	points = []
	for x, y in arrow:
		points.append((x*canvas.winfo_width(), y*canvas.winfo_height()))
	canvas_arrow_ids.append(canvas.create_line(*points, fill=color, arrow="last", width=2))

def robinson_projection(lon, lat):
	lookup_index = abs(int(lat)) // 5
	remainder = (abs(lat) % 5) / 5
	X = ROBINSON_PROJECTION_TABLE[lookup_index] + remainder*(ROBINSON_PROJECTION_TABLE[lookup_index + 1] - ROBINSON_PROJECTION_TABLE[lookup_index])
	x = (180 + X*lon)/360
	y = (81-lat)/162
	return x, y

label_text = ""
label = tk.Label(root, bg=BG_COLOR, fg=FG_COLOR, font="monospace 12", anchor="sw", justify=tk.LEFT)
label.grid(column=1, row=0, sticky="NSEW")

def print_to_label(line):
	global label_text
	label_text += line
	label.config(text=label_text)

entry = tk.Entry(root, bg=BG_COLOR, fg=FG_COLOR, width=15, font="monospace 24", highlightbackground=FG_DARK, highlightcolor=FG_COLOR)
entry.grid(column=1, row=1, sticky="NSEW")

def highlight_country(country, color):
	highlighted_countries[country] = color
	for polygon in canvas_countries[country]:
		canvas.itemconfig(polygon, fill=color)
def unhighlight_country(country):
	#highlighted_countries.pop(country, None)
	for polygon in canvas_countries[country]:
		canvas.itemconfig(polygon, fill=COUNTRY_FILL)

traceroute_in_progress = False
def traceroute(event):
	global traceroute_in_progress, canvas_point_ids, canvas_arrow_ids, highlighted_countries, canvas_points, canvas_arrows
	
	if traceroute_in_progress:
		return
	traceroute_in_progress = True

	for point_id in canvas_point_ids:
		canvas.delete(point_id)
	for arrow_id in canvas_arrow_ids:
		canvas.delete(arrow_id)
	for country in highlighted_countries:
		unhighlight_country(country)
	canvas_point_ids = []
	canvas_arrow_ids = []
	canvas_points = []
	canvas_arrows = []
	highlighted_countries = {}
	root.update()

	ip = entry.get()
	process = subprocess.Popen(["traceroute", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	last_point = ()
	for line in process.stdout:
		if re.search("..\\ \\ .+[0-9].*", line) != None:
			current_ip = line.split("(")[1].split(")")[0]
			print_to_label(current_ip)
			location = subprocess.check_output(f"./geoloc {current_ip}", shell=True, text=True)
			if location == "":
				print_to_label(" No location\n")
			else:
				location_data = location.split(",")
				print_to_label(f" {location_data[0]}-{location_data[1]}\n")
				lat, lon = location_data[2:4]
				lat = float(lat)
				lon = float(lon)

				if location_data[0] in canvas_countries:
					highlight_country(location_data[0], COUNTRY_HIGHLIGHT)

				if last_point != ():
					draw_arrow(*last_point, lon, lat)
					for i in range(len(canvas_arrow_ids)):
						interpolation = i/max(len(canvas_arrow_ids)-1, 1)
						color_rgb = [int(CONNECTION_START_RGB[j] + interpolation*CONNECTION_DIFF_RGB[j]) for j in range(3)]
						color = "#"
						for j in range(3):
							component = hex(color_rgb[j])[2:]
							if len(component) < 2:
								component = "0" + component
							color += component
						canvas.itemconfig(canvas_arrow_ids[i], fill=color)

				draw_point(*robinson_projection(lon, lat))
				last_point = (lon, lat)
			root.update()

	process.wait()
	print_to_label("\n- - - finished - - -")
	traceroute_in_progress = False
	

entry.bind("<Return>", traceroute)



root.update()
label.config(wraplength=label.winfo_width())

root.mainloop()







