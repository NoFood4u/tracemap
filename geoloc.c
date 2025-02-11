#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<unistd.h>

void printInfo(char* line)
{
	const char* tok;
	int i = 0;
	for (tok = strtok(line, ","); tok && *tok; tok = strtok(NULL, ",\n")) {
		switch (i) {
			case 2:
				printf("%s", tok);
				break;
			case 4:
				printf(",%s", tok);
				break;
			case 5:
				printf(",%s", tok);
				break;
			case 6:
				printf(",%s", tok);
				return;
		}
		i++;
	}
	return;
}

int isInRange(char* line, int x)
{
	unsigned int range[2];
	const char* tok;
	int i = 0;
	for (tok = strtok(line, ","); tok && *tok; tok = strtok(NULL, ",\n")) {
		range[i] = atoi(tok);
		if (i++ == 1) {
			return x >= range[0] && x <= range[1];
		}
	}
	return 0;
}

int main(int argc, char *argv[]) { 
	// parse flags/options
	int opt; 
	while ((opt = getopt(argc, argv, ":if:lrx")) != -1) {
		switch (opt) {
			case 'i':  
			case 'l':  
			case 'r':  
				printf("option: %c\n", opt);  
				break;  
			case 'f':  
				printf("filename: %s\n", optarg);  
				break;  
			case ':':  
				printf("option needs a value\n");  
				break;  
			case '?':  
				printf("unknown option: %c\n", optopt); 
				break;  
		}
	}
	// get input ip
	if (argc - optind != 1) {
		printf("unexpected number of arguments, exected 1 but got %d", argc - optind);
		return 1;
	}
	unsigned int ip = 0;
	int i = 24;
	for (char* tok = strtok(argv[1], "."); tok && *tok; tok = strtok(NULL, ".")) {
		unsigned int component = atoi(tok);
		if (component < 0 || component > 255) {
			printf("Incorrect IPv4 format.");
			return 1;
		}
		ip += component << i;
		i -= 8;
	}
	if (i != -8) {
		printf("Incorrect IPv4 format.");
		return 1;
	}

	// database lookup
	FILE* stream = fopen("dbip-city-ipv4-num.csv", "r");
	const int NUM_RECORDS = 3275051;
	char line[1024];
	while (fgets(line, 1024, stream))
	{
		char* tmp = strdup(line);
		if (isInRange(tmp, ip)) {
			printInfo(line);
			break;
		}
		free(tmp);
	}
	
	return 0;
}
