# OpenOps

Scrpits for maintaining and trobleshooting Openstack

## Prerequisite

```bash

$ sudo apt install -y python-dev python-pip

$ for COMP in `echo "keystone nova cinder glance neutron"`; do sudo pip install python-"$COMP"client; done

$ pip freeze | awk -F '==' '{print $1}' | xargs -n 1 sudo pip install -U

```

## Usage

```bash
$ python openstack/admin.py $INSTANCE_ID

```

## Development and Contribution

Questions and pull requests are always welcome!

Source Repository
https://github.com/itisnotdone/openops

Issues and questions
https://github.com/itisnotdone/openops/issues


## License

The gem is available as open source under the terms of the [MIT License](http://opensource.org/licenses/MIT).

