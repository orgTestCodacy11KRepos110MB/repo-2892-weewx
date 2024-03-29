#!/usr/bin/env python
#
#    Copyright (c) 2009-2023 Tom Keffer <tkeffer@gmail.com>
#
#    See the file LICENSE.txt for your rights.
#
"""Executable that can run all reports."""

import argparse
import importlib
import socket
import sys
import time

import weecfg
import weeutil.logger
import weewx
import weewx.engine
import weewx.manager
import weewx.reportengine
import weewx.station
from weeutil.weeutil import timestamp_to_string

description = """Run all reports defined in the specified configuration file.
Use this utility to run reports immediately instead of waiting for the end of
an archive interval."""

usage = """%(prog)s --help
       %(prog)s [CONFIG_FILE | --config=CONFIG_FILE]
       %(prog)s [CONFIG_FILE | --config=CONFIG_FILE] --epoch=TIMESTAMP
       %(prog)s [CONFIG_FILE | --config=CONFIG_FILE] --date=YYYY-MM-DD --time=HH:MM"""

epilog = "Specify either the positional argument CONFIG_FILE, " \
         "or the optional argument --config, but not both."


def disable_timing(section, key):
    """Function to effectively disable report_timing option"""
    if key == 'report_timing':
        section['report_timing'] = "* * * * *"


def main():
    # Create a command line parser:
    parser = argparse.ArgumentParser(description=description, usage=usage, epilog=epilog,
                                     prog='wee_reports')

    # Add the various options:
    parser.add_argument("--config", dest="config_option", metavar="CONFIG_FILE",
                        help="Use the configuration file CONFIG_FILE")
    parser.add_argument("--epoch", metavar="EPOCH_TIME",
                        help="Time of the report in unix epoch time")
    parser.add_argument("--date", metavar="YYYY-MM-DD",
                        type=lambda d: time.strptime(d, '%Y-%m-%d'),
                        help="Date for the report")
    parser.add_argument("--time", metavar="HH:MM",
                        type=lambda t: time.strptime(t, '%H:%M'),
                        help="Time of day for the report")
    parser.add_argument("config_arg", nargs='?', metavar="CONFIG_FILE")

    # Now we are ready to parse the command line:
    namespace = parser.parse_args()

    # User can specify the config file as either a positional argument, or as an option
    # argument, but not both.
    if namespace.config_option and namespace.config_arg:
        sys.exit(epilog)
    # Presence of --date requires --time and v.v.
    if namespace.date and not namespace.time or namespace.time and not namespace.date:
        sys.exit("Must specify both --date and --time.")
    # Can specify the time as either unix epoch time, or explicit date and time, but not both
    if namespace.epoch and namespace.date:
        sys.exit("The time of the report must be specified either as unix epoch time, "
                 "or with an explicit date and time, but not both.")

    # If the user specified a time, retrieve it. Otherwise, set to None
    if namespace.epoch:
        gen_ts = int(namespace.epoch)
    elif namespace.date:
        gen_ts = get_epoch_time(namespace.date, namespace.time)
    else:
        gen_ts = None

    if gen_ts is None:
        print("Generating as of last timestamp in the database.")
    else:
        print("Generating for requested time %s" % timestamp_to_string(gen_ts))

    # Fetch the config file
    config_path, config_dict = weecfg.read_config(namespace.config_arg, [namespace.config_option])
    print("Using configuration file %s" % config_path)

    # Now that we have the configuration dictionary, we can add the path to the user
    # directory to PYTHONPATH.
    weewx.add_user_path(config_dict)
    # Now we can import user extensions
    importlib.import_module('user.extensions')

    # Look for the debug flag. If set, ask for extra logging
    weewx.debug = int(config_dict.get('debug', 0))

    # Set logging configuration:
    weeutil.logger.setup('wee_reports', config_dict)

    # For wee_reports we want to generate all reports irrespective of any
    # report_timing settings that may exist. The easiest way to do this is walk
    # the config dict resetting any report_timing settings found.
    config_dict.walk(disable_timing)

    socket.setdefaulttimeout(10)

    # Instantiate the dummy engine. This will cause services to get loaded, which will make
    # the type extensions (xtypes) system available.
    engine = weewx.engine.DummyEngine(config_dict)

    stn_info = weewx.station.StationInfo(**config_dict['Station'])

    try:
        binding = config_dict['StdArchive']['data_binding']
    except KeyError:
        binding = 'wx_binding'

    # Retrieve the appropriate record from the database
    with weewx.manager.DBBinder(config_dict) as db_binder:
        db_manager = db_binder.get_manager(binding)
        if gen_ts:
            ts = gen_ts
        else:
            ts = db_manager.lastGoodStamp()

        record = db_manager.getRecord(ts)

    # Instantiate the report engine with the retrieved record and required timestamp
    t = weewx.reportengine.StdReportEngine(config_dict, stn_info, record=record, gen_ts=ts)

    # Although the report engine inherits from Thread, we can just run it in the main thread:
    t.run()

    # Shut down any running services, 
    engine.shutDown()


def get_epoch_time(d_tt, t_tt):
    tt = (d_tt.tm_year, d_tt.tm_mon, d_tt.tm_mday,
          t_tt.tm_hour, t_tt.tm_min, 0, 0, 0, -1)
    return time.mktime(tt)


if __name__ == "__main__":
    main()
