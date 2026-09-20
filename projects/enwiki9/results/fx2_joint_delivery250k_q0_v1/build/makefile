all: comp9

comp9:
	$(MAKE) -C native -j1 cmix CC=/usr/bin/g++ 'CPPFLAGS_PART-THAT-SHOULD-BE-FAST=-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections -O3' 'CPPFLAGS_PART-THAT-CAN-BE-SLOW=-DSEED=923 -DUPDATE_LIMIT=3000 -m64 -Wall -std=c++17 -include cstdint -fno-fast-math -fno-math-errno -fno-exceptions -fno-threadsafe-statics -march=x86-64-v3 -mtune=generic -mrecip=none -fdata-sections -ffunction-sections -Os'
	/usr/bin/g++ -std=c++17 -Os -s envelope.cpp -o envelope
	python3 pack.py

clean:
	$(MAKE) -C native clean
	rm -f comp9 envelope
