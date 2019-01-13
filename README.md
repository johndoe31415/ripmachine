# ripmachine
I've had a ton of CDs and DVDs that I needed to archive in order to throw them
away. To rip them all I built myself a rig with six CD/DVD drives and used a
web-based UI to rip them. Now I'm in a similar situation and I'm reimplementing
the super-shoddy implementation from years ago here.

## Dependencies
The UI uses Python3, mako and uwsgi. The ripdisc relies on dd_rescue and
cdparanoia. Possible postprocessing tools coming later.

## License
GNU GPL-3. 
