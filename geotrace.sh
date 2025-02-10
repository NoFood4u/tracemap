route=$(traceroute $1)
ips=()
while IFS= read -r line; do
		if [[ $line =~ ..\ \ .+[0-9].* ]]; then
			ips+=($(echo $line | cut -d '(' -f2 | cut -d ')' -f1))
		fi
done <<< "$route"
echo
for ip in ${ips[*]}; do
	./a.out $ip
	echo " $ip"
done
