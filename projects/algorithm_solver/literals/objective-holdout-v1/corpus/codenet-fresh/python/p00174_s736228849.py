while True:
	str = input();
	if (str == '0'):
		break;
	
	scorea = 0;
	scoreb = 0;
	for i in range(1, len(str)):
		if (str[i] == 'A'):
			scorea += 1;
		else:
			scoreb += 1;
	
	if (scorea > scoreb):
		scorea += 1;
	else:
		scoreb += 1;
	
	print(scorea, scoreb);