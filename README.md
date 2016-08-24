Alright, bear with me. The code is terrible, and buggy, and requires some patches to Chirp, and my fork of md380tools.


The chirp symlink should point to the `chirp_fork/chirp/` directory if using my chirp fork.

The md380tools symlink should point to your md380tools repository. Or, rather, mine. (I should work on that.)

The drivers/ directory should have a symlink to the `md380tools/chirp/md380.py` driver.

You can try and run this (It's a really basic "shell" for managing DMR radios) with `./dmr-programmer` and it will probably fail. 

If it doesn't fail, hopefully it can explain itself enough to be used.



