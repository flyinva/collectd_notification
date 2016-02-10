# Description

This module can send collectd notification to:

 - NSCA (for Nagios, Icinga, Shinken, etc.)
 - a JSON file

# Usage with collectd

Add this in ``collectd.conf``:

```
<Plugin python>
			ModulePath "/WHERE/YOU/WANT/collectd_notification"
			Import "collectd_notification"
			<Module collectd_notification>
							timer 300
							nsca true
							status true
							status_file "/var/lib/collectd/status.json"
			</Module>
</Plugin>

```
