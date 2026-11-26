while True:
	try:
		line=list(map(str,input()))
		string=""
		for i in range(len(line)):
			if (line[i]!='@' and line[i-1]!='@' and line[i-2]!='@'):
				string+=line[i]
			elif line[i]=='@':
				string+=line[i+2]*int(line[i+1])
			else:
				pass
		print(string)
	except EOFError:
		break
		
				