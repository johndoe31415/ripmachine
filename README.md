# ripmachine
I've had a ton of CDs and DVDs that I needed to archive in order to throw them
away. To rip them all I built myself a rig with six CD/DVD drives and used a
web-based UI to rip them. Now I'm in a similar situation and I'm reimplementing
the super-shoddy implementation from years ago here.

## Dependencies
For the UI, the following packages are needed:
  * Python 3
  * python3-mako
  * uwsgi

For ripdisc, the following tools are relied upon:
  * dd_rescue
  * cdparanoia
  * libcdio
  * wodim
  * mplayer

For rippostproc, these are the dependencies that are necessary:
  * flac

Here's a quick way to install dependencies on a Ubuntu machine:

```
# apt-get update
# apt-get install python3 python3-mako mplayer cdparanoia dd_rescue libcdio-utils wodim flac
```

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
