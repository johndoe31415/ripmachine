# ripmachine
I've had a ton of CDs and DVDs that I needed to archive in order to throw them
away. To rip them all I built myself a rig with six CD/DVD drives and used a
web-based UI to rip them. Now I'm in a similar situation and I'm reimplementing
the super-shoddy implementation from years ago here.

## Dependencies
The UI uses Python3, mako and uwsgi. The ripdisc relies on dd_rescue and
cdparanoia. Possible postprocessing tools coming later.

## Included third-party code
ripgui includes the file progressbar.min.js from
[progressbar.js](https://github.com/kimmobrunfeldt/progressbar.js) which is
licensed under the MIT license.

apt-get install cdparanoia libcdio-utils genisoimage

# Included
Icons: https://feathericons.com/
Spinner: by Sam Herbert (@sherb), for everyone. More @ http://goo.gl/7AJzbL
sprintf: TODO

## License
GNU GPL-3. 
