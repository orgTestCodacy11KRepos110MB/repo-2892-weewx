# The Cheetah generator

This section gives an overview of the Cheetah generator. For details about each of its various options, see the section [_[CheetahGenerator]_](../options_ref#CheetahGenerator) in [_Reference: report options_](../options_ref).

File generation is done using the [Cheetah](https://cheetahtemplate.org/) templating engine, which processes a _template_, replacing any symbolic _tags_, then produces an output file. Typically, it runs after each new archive record (usually about every five minutes), but it can also run on demand using the utility `wee_reports`.

The Cheetah engine is very powerful, essentially letting you have the full semantics of Python available in your templates. As this would make the templates incomprehensible to anyone but a Python programmer, WeeWX adopts a very small subset of its power.

The Cheetah generator is controlled by the section  [_[CheetahGenerator]_](../options_ref#CheetahGenerator). Let's take a look at how this works.

## Which files get processed?

Each template file is named something like `D/F.E.tmpl`, where `D` is the (optional) directory the template sits in and will also be the directory the results will be put in, and `F.E` is the generated file name. So, given a template file with name `Acme/index.html.tmpl`, the results will be put in <code><em>HTML_ROOT</em>/Acme/index.html</code>.

The configuration for a group of templates will look something like this:

```init
[CheetahGenerator]
    [[index]]
        template = index.html.tmpl
    [[textfile]]
        template = filename.txt.tmpl
    [[xmlfile]]
        template = filename.xml.tmpl
```

There can be only one template in each block. In most cases, the block name does not matter — it is used only to isolate each template. However, there are four block names that have special meaning: `SummaryByDay`, `SummaryByMonth`, `SummaryByYear`, and `ToDate`.

### Specifying template files

By way of example, here is the `[CheetahGenerator]` section from the `skin.conf` for the skin _`Seasons`_.

```ini linenums="1"
[CheetahGenerator]
    # The CheetahGenerator creates files from templates.  This section
    # specifies which files will be generated from which template.

    # Possible encodings include 'html_entities', 'strict_ascii', 'normalized_ascii',
    # as well as those listed in https://docs.python.org/3/library/codecs.html#standard-encodings
    encoding = html_entities

    [[SummaryByMonth]]
        # Reports that summarize "by month"
        [[[NOAA_month]]]
            encoding = normalized_ascii
            template = NOAA/NOAA-%Y-%m.txt.tmpl

    [[SummaryByYear]]
        # Reports that summarize "by year"
        [[[NOAA_year]]]
            encoding = normalized_ascii
            template = NOAA/NOAA-%Y.txt.tmpl

    [[ToDate]]
        # Reports that show statistics "to date", such as day-to-date,
        # week-to-date, month-to-date, etc.
        [[[index]]]
            template = index.html.tmpl
        [[[statistics]]]
            template = statistics.html.tmpl
        [[[telemetry]]]
            template = telemetry.html.tmpl
        [[[tabular]]]
            template = tabular.html.tmpl
        [[[celestial]]]
            template = celestial.html.tmpl
            # Uncomment the following to have WeeWX generate a celestial page only once an hour:
            # stale_age = 3600
        [[[RSS]]]
            template = rss.xml.tmpl
```    

The skin contains three different kinds of generated output:

1.  Summary by Month (line 9). The skin uses `SummaryByMonth` to produce NOAA summaries, one for each month, as a simple text file.
2.  Summary by Year (line 15). The skin uses `SummaryByYear` to produce NOAA summaries, one for each year, as a simple text file.
3.  Summary "To Date" (line 21). The skin produces an HTML `index.html` page, as well as HTML files for detailed statistics, telemetry, and celestial information. It also includes a master page (`tabular.html`) in which NOAA information is displayed. All these files are HTML.

Because the option

        encoding = html_entities

appears directly under `[StdReport]`, this will be the default encoding of the generated files unless explicitly overridden. We see an example of this under `[SummaryByMonth]` and `[SummaryByYear]`, which use option `normalized_ascii` instead of `html_entities`. This encoding replaces accented characters with a non-accented analog.

Other than `SummaryByMonth` and `SummaryByYear`, the section names are arbitrary. The section `ToDate` could just as well have been called `files_to_date`, and the sections `index`, `statistics`, and `telemetry` could just as well have been called `tom`, `dick`, and `harry`.

### `[[SummaryByYear]]`

Use `SummaryByYear` to generate a set of files, one file per year. The name of the template file should contain a [strftime()](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) code for the year; this will be replaced with the year of the data in the file.

```ini
[CheetahGenerator]
    [[SummaryByYear]]
        # Reports that summarize "by year"
        [[[NOAA_year]]]
            encoding = normalized_ascii
            template = NOAA/NOAA-%Y.txt.tmpl
```

The template `NOAA/NOAA-%Y.txt.tmpl` might look something like this:

```
           SUMMARY FOR YEAR $year.dateTime

MONTHLY TEMPERATURES AND HUMIDITIES:
#for $record in $year.records
$record.dateTime $record.outTemp $record.outHumidity
#end for
```    

### `[[SummaryByMonth]]`

Use `SummaryByMonth` to generate a set of files, one file per month. The name of the template file should contain a [strftime()](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) code for year and month; these will be replaced with the year and month of the data in the file.

```ini
[CheetahGenerator]
    [[SummaryByMonth]]
        # Reports that summarize "by month"
        [[[NOAA_month]]]
            encoding = normalized_ascii
            template = NOAA/NOAA-%Y-%m.txt.tmpl
```

The template `NOAA/NOAA-%Y-%m.txt.tmpl` might look something like this:

```
           SUMMARY FOR MONTH $month.dateTime

DAILY TEMPERATURES AND HUMIDITIES:
#for $record in $month.records
$record.dateTime $record.outTemp $record.outHumidity
#end for
```

### `[[SummaryByDay]]`

While the _Seasons_ skin does not make use of it, there is also a `SummaryByDay` capability. As the name suggests, this results in one file per day. The name of the template file should contain a [strftime()](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) code for the year, month and day; these will be replaced with the year, month, and day of the data in the file.

```init
[CheetahGenerator]
    [[SummaryByDay]]
        # Reports that summarize "by day"
        [[[NOAA_day]]]
            encoding = normalized_ascii
            template = NOAA/NOAA-%Y-%m-%d.txt.tmpl
```

The template `NOAA/NOAA-%Y-%m-%d.txt.tmpl` might look something like this:

```
           SUMMARY FOR DAY $day.dateTime

HOURLY TEMPERATURES AND HUMIDITIES:
#for $record in $day.records
$record.dateTime $record.outTemp $record.outHumidity
#end for
```

!!! Note
    This can create a _lot_ of files &mdash; one per day. If you have 3 years of records, this would be more than 1,000 files!



## Tags

If you look inside a template, you will see it makes heavy use of _tags_. As the Cheetah generator processes the template, it replaces each tag with an appropriate value and, sometimes, a label. This section discusses the details of how that happens.

If there is a tag error during template generation, the error will show up in the log file. Many errors are obvious — Cheetah will display a line number and list the template file in which the error occurred. Unfortunately, in other cases, the error message can be very cryptic and not very useful. So make small changes and test often. Use the utility [wee_reports](../../../utilities/utilities.htm#wee_reports_utility) to speed up the process.

Here are some examples of tags:

```
$current.outTemp
$month.outTemp.max
$month.outTemp.maxtime
```

These code the current outside temperature, the maximum outside temperature for the month, and the time that maximum occurred, respectively. So a template file that contains:

```html
<html>
    <head>
        <title>Current conditions</title>
    </head>
    <body>
        <p>Current temperature = $current.outTemp</p>
        <p>Max for the month is $month.outTemp.max, which occurred at $month.outTemp.maxtime</p>
    </body>
</html>
```

would be all you need for a very simple HTML page that would display the text (assuming that the unit group for temperature is `degree_F`):

<span class="example_output">
Current temperature = 51.0°F  
Max for the month is 68.8°F, which occurred at 07-Oct-2009 15:15
</span>

The format that was used to format the temperature (`51.0`) is specified in section [[Units][[StringFormat]]](../options_ref/#Units_StringFormats). The unit label `°F` is from section [[Units][[Labels]]](../options_ref/#Units_Labels), while the time format is from [[Units][[TimeFormats]]](../options_ref/#Units_TimeFormats).

As we saw above, the tags can be very simple:

```
# Output max outside temperature using an appropriate format and label:
$month.outTemp.max
```

Most of the time, tags will "do the right thing" and are all you will need. However, WeeWX offers extensive customization of the tags for specialized applications such as XML RSS feeds, or rigidly formatted reports (such as the NOAA reports). This section specifies the various tag options available.

There are two different versions of the tags, depending on whether the data is "current", or an aggregation over time. However, both versions are similar.

### Time period `$current`

Time period `$current` represents a _current observation_. An example would be the current barometric pressure:

    $current.barometer

Formally, for current observations, WeeWX first looks for the observation type in the record emitted by the `NEW_ARCHIVE_RECORD` event. This is generally the data emitted by the station console, augmented by any derived variables (_e.g._ wind chill) that you might have specified. If the observation type cannot be found there, the most recent record in the database will be searched.

The most general tag for a "current" observation looks like:

    $current($timestamp=some_time, $max_delta=delta_t,$data_binding=binding_name).obstype[.optional_unit_conversion][.optional_rounding][.optional_formatting]

Where:

_`$timestamp`_ is a timestamp that you want to display in unix epoch time. It is optional, The default is to display the value for the current time.

_`$max_delta`_ is the largest acceptable time difference (in seconds) between the time specified by `$timestamp` and a record's timestamp in the database. By default, it is zero, which means there must be an exact match with a specified time for a record to be retrieved. If it were `30`, then a record up to 30 seconds away would be acceptable.

_`$data_binding`_ is a _binding name_ to a database. An example would be `wx_binding`. See the section _[Binding names](../../custom#binding-names)_ for more details.

_`obstype`_ is an observation type, such as `barometer`. This type must appear either as a field in the database, or in the current (usually, the latest) record.

_`optional_unit_conversion`_ is an optional unit conversion tag. If provided, the results will be converted into the specified units, otherwise the default units specified in the skin configuration file (in section `[Units][[Groups]]`) will be used. See the section _[Unit conversion options](#unit-conversion-options)_.

_`optional_rounding`_ allows the results to be rounded to a fixed number of decimal digits. See the section _[Optional rounding](#optional-rounding)_.

_`optional_formatting`_ is a set of optional formatting tags, which control how the value will appear. See the section _[Formatting options](#formatting-options)_ below.

### Time period $latest

Time period `$latest` is very similar to `$current`, except that it uses the last available timestamp in a database. Usually, `$current` and `$latest` are the same, but if a data binding points to a remote database, they may not be. See the section _[Using multiple bindings](../multiple_bindings)_ for an example where this happened.

### Aggregation periods

Aggregation periods is the other kind of tag. For example,

    $week.rain.sum

represents an _aggregation over time_, using a certain _aggregation type_. In this example, the aggregation time is a week, and the aggregation type is summation. So, this tag represents the total rainfall over a week.

The most general tag for an aggregation over time looks like:

    $period($data_binding=binding_name, $optional_ago=_delta).statstype.aggregation[.optional_unit_conversion][.optional_rounding][.optional_formatting]

Where:

_`period`_ is the time period over which the aggregation is to be done. Possible choices are listed in the [table below](#aggregation_periods).

_`data_binding`_ is a _binding name_ to a database. An example would be `wx_binding`. See the section _[Binding names](../../custom#binding-names)_ for more details.

_`optional_ago`_ is a keyword that depends on the aggregation period. For example, for week, it would be `weeks_ago`, for day, it would be `days_ago`, _etc._

_`delta`_ is an integer indicating which aggregation period is desired. For example `$week($weeks_ago=1)` indicates last week, `$day($days_ago=2)` would be the day-before-yesterday, _etc_. The default is zero: that is, this aggregation period.

_`statstype`_ is a _statistical type_. This is generally any observation type that appears in the database, as well as a few synthetic types (such as heating and cooling degree-days). Not all aggregations are supported for all types.

_`aggregation`_ is an _aggregation type_. If you ask for `$month.outTemp.avg` you are asking for the _average_ outside temperature for the month. Possible aggregation types are given in _[Appendix: Aggregation types](../appendix/#aggregation_types)_.

_`optional_unit_conversion`_ is an optional unit conversion tag. If provided, the results will be converted into the specified units, otherwise the default units specified in the skin configuration file (in section `[Units][[Groups]]`) will be used. See the section _[Unit conversion options](#unit-conversion-options)_.

_`optional_rounding`_ allows the results to be rounded to a fixed number of decimal digits. See the section _[Optional rounding](#optional-rounding)_

_`optional_formatting`_ is a set of optional formatting tags, which control how the value will appear. See the section _[Formatting options](#formatting-options)_ below.

There are several _aggregation periods_ that can be used:

<table id="aggregation_periods" class="indent">
    <caption>Aggregation periods</caption>
    <tbody>
    <tr class="first_row">
        <td>Aggregation period</td>
        <td>Meaning</td>
        <td>Example</td>
        <td>Meaning of example</td>
    </tr>
    <tr>
        <td class="first_col code">$hour</td>
        <td>This hour.</td>
        <td class="code">$hour.outTemp.maxtime</td>
        <td>The time of the max temperature this hour.</td>
    </tr>
    <tr>
        <td class="first_col code">$day</td>
        <td>Today (since midnight).</td>
        <td class="code">$day.outTemp.max</td>
        <td>The max temperature since midnight</td>
    </tr>
    <tr>
        <td class="first_col code">$yesterday</td>
        <td>Yesterday. Synonym for <span class="code">$day($days_ago=1)</span>.
        </td>
        <td class="code">$yesterday.outTemp.maxtime</td>
        <td>The time of the max temperature yesterday.</td>
    </tr>
    <tr>
        <td class="first_col code">$week</td>
        <td>This week. The start of the week is set by option <a href="../../usersguide/weewx-config-file/stations-config#week_start"><span
            class="code">week_start</span></a>.
        </td>
        <td class="code">$week.outTemp.max</td>
        <td>The max temperature this week.</td>
    </tr>
    <tr>
        <td class="first_col code">$month</td>
        <td>This month (since the first of the month).</td>
        <td class="code">$month.outTemp.min</td>
        <td>The minimum temperature this month.</td>
    </tr>
    <tr>
        <td class="first_col code">$year</td>
        <td>This year (since 1-Jan).</td>
        <td class="code">$year.outTemp.max</td>
        <td>The max temperature since the start of the year.</td>
    </tr>
    <tr>
        <td class="first_col code">$rainyear</td>
        <td>This rain year. The start of the rain year is set by option <a
            href="../../usersguide/weewx-config-file/stations-config#rain_year_start"><span class="code">rain_year_start</span></a>.
        </td>
        <td class="code">$rainyear.rain.sum</td>
        <td>The total rainfall for this rain year. </td>
    </tr>
    <tr>
        <td class="first_col code">$alltime</td>
        <td>
            All records in the database given by <span class="code"><em>binding_name</em></span>.
        </td>
        <td class="code">$alltime.outTemp.max</td>
        <td>
            The maximum outside temperature in the default database.
        </td>
    </tr>

    </tbody>
</table>

The _`$optional_ago`_ parameters can be useful for statistics farther in the past. Here are some examples:

<table class="indent">
    <tbody>
    <tr class="first_row">
        <td>Aggregation period</td>
        <td>Example</td>
        <td>Meaning</td>
    </tr>
    <tr>
        <td class="first_col code">$hour($hours_ago=<em>h</em>)
        </td>
        <td class="code">$hour($hours_ago=1).outTemp.avg</td>
        <td>The average temperature last hour (1 hour ago).</td>
    </tr>
    <tr>
        <td class="first_col code">$day($days_ago=<em>d</em>)
        </td>
        <td class="code">$day($days_ago=2).outTemp.avg</td>
        <td>The average temperature day before yesterday (2 days ago).
        </td>
    </tr>
    <tr>
        <td class="first_col code">$week($weeks_ago=<em>d</em>)
        </td>
        <td class="code">$week($weeks_ago=1).outTemp.max</td>
        <td>The maximum temperature last week.</td>
    </tr>
    <tr>
        <td class="first_col code">$month($months_ago=<em>m</em>)
        </td>
        <td class="code">$month($months_ago=1).outTemp.max</td>
        <td>The maximum temperature last month.</td>
    </tr>
    <tr>
        <td class="first_col code">$year($years_ago=<em>m</em>)
        </td>
        <td class="code">$year($years_ago=1).outTemp.max</td>
        <td>The maximum temperature last year.</td>
    </tr>
    </tbody>
</table>

## Unit conversion options

The tag _`optional_unit_conversion`_ can be used with either current observations or aggregations. If supplied, the results will be converted to the specified units. For example, if you have set `group_pressure` to inches of mercury (`inHg`), then the tag

    Today's average pressure=$day.barometer.avg 

would normally give a result such as

<div class="example_output">
Today's average pressure=30.05 inHg
</div>

However, if you add `mbar` to the end of the tag,

    Today's average pressure=$day.barometer.avg.mbar

then the results will be in millibars:

<div class="example_output">
Today's average pressure=1017.5 mbar
</div>

#### Illegal conversions

If an inappropriate or nonsense conversion is asked for, _e.g._,

```
Today's minimum pressure in mbars: $day.barometer.min.mbar
or in degrees C: $day.barometer.min.degree_C
or in foobar units: $day.barometer.min.foobar
```

then the offending tag(s) will be put in the output:

<div class="example_output">
Today's minimum pressure in mbars: 1015.3  
or in degrees C: $day.barometer.min.degree_C  
or in foobar units: $day.barometer.min.foobar
</div>

### Optional rounding

The data in the resultant tag can be optionally rounded to a fixed number of decimal digits. This is useful when emitting raw data or JSON strings. It should _not_ be used with formatted data (using a [format string](#format_string) would be a better choice).

The structure of the tag is

    .round(ndigits=None)

where `ndigits` is the number of decimal digits to retain. If `None` (the default), then all digits will be retained.

## Formatting options

A variety of tags and arguments are available to you to customize the formatting of the final observation value. This table lists the tags:

<table class="indent">
    <caption>Optional formatting tag</caption>
    <tbody>
    <tr class="first_row">
        <td>Optional formatting tag</td>
        <td>Comment</td>
    </tr>
    <tr>
        <td class="code text_highlight">.format(<em>args</em>)</td>
        <td>Format the value as a string, according to a set of optional <em>args</em> (see below).</td>
    </tr>
    <tr>
        <td class="code text_highlight">.ordinal_compass</td>
        <td>Format the value as a compass ordinals (<i>e.g.</i>"SW"), useful for wind directions.
            The ordinal abbreviations are set by option <a href="../options_ref/#Units_Ordinates"><span class="code">directions</span></a> in the skin
            configuration file <span class="code">skin.conf</span>.
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">.long_form</td>
        <td>
            Format delta times in the "long form". A "delta time" is the difference between two times. An
            example is the amount of uptime (difference between start and current time). By default, this will
            be formatted as the number of elapsed seconds (<em>e.g.,</em> <span
            class="code">45000 seconds</span>). The "long form" breaks the time down into constituent time
            elements (<em>e.g.,</em> <span class="code">12 hours, 30 minutes, 0 seconds</span>).
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">.json</td>
        <td>
            Format the value as a <a href="https://www.json.org/json-en.html">JSON string</a>.
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">.raw</td>
        <td>Return the value "as is", without being converted to a string and without any formatting applied.
            This can be useful for doing arithmetic directly within the templates. You must be prepared to deal
            with a potential <span class="code">None</span> value.
        </td>
    </tr>
    </tbody>
</table>


The first of these tags (.format()) has the formal structure:

    .format(format_string=None, None_string=None, add_label=True, localize=True)

Here is the meaning of each of the optional arguments:

<table class="indent">
    <caption>Optional arguments for <span class="code">.format()</span></caption>
    <tbody>
    <tr class="first_row">
        <td>Optional argument</td>
        <td>Comment</td>
    </tr>
    <tr>
        <td id="format_string" class='code text_highlight'>format_string</td>
        <td>Use the optional string to format the value. If set to <span class="code">None</span>, then an
            appropriate string format from <span class="code">skin.conf</span> will be used.
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">None_string</td>
        <td>Should the observation value be <span class="code">NONE</span>, then use the supplied string
            (typically, something like "N/A"). If <span class="code">None_string</span> is set to <span
                class="code">None</span>, then the value for <span class="code">NONE</span> in <span
                class="code"> <a href="../options_ref/#Units_StringFormats">[Units][[StringFormats]]</a>
      </span> will be used.
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">add_label</td>
        <td>If set to <span class="code">True</span> (the default), then a unit label (<i>e.g.</i>, &deg;F) from
            <span class="code">skin.conf</span> will be attached to the end. Otherwise, it will be left out.
        </td>
    </tr>
    <tr>
        <td class="code text_highlight">localize</td>
        <td>If set to <span class="code">True</span> (the default), then localize the results. Otherwise, do
            not.
        </td>
    </tr>
    </tbody>
</table>

If you're willing to honor the ordering of the arguments, the argument name can be omitted.

### Formatting examples

This section gives a number of example tags, and their expected output. The following values are assumed:

<table class="indent" style="width:50%">
    <caption>Values used in the examples below</caption>
    <tr class="first_row">
        <td>Observation</td>
        <td>Value</td>
    </tr>
    <tr>
        <td class="code first_col">
            outTemp
        </td>
        <td>45.2&deg;F</td>
    </tr>
    <tr>
        <td class="code first_col">
            UV
        </td>
        <td>
            <span class="code">None</span>
        </td>
    </tr>
    <tr>
        <td class="code first_col">
            windDir
        </td>
        <td>138&deg;</td>
    </tr>
    <tr>
        <td class="code first_col">
            dateTime
        </td>
        <td>1270250700</td>
    </tr>
</table>

Here are the examples:

<table>
    <caption>Formatting options with expected results</caption>
    <tbody>
    <tr class="first_row">
        <td>Tag</td>
        <td>Result</td>
        <td>Result<br/>type</td>
        <td>Comment</td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp</td>
        <td class="code">45.2°F</td>
        <td class="code">str</td>
        <td>
            String formatting from <span class="code"><a
            href="../options_ref/#Units_StringFormats">[Units][[StringFormats]]"</a></span>. Label from <span class="code"><a
            href="../options_ref/#Units_Labels">[Units][[Labels]]"</a></span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.format</td>
        <td class="code">45.2°F</td>
        <td class="code">str</td>
        <td>
            Same as the <span class="code">$current.outTemp</span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.format()</td>
        <td class="code">45.2°F</td>
        <td class="code">str</td>
        <td>
            Same as the <span class="code">$current.outTemp</span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.format(format_string="%.3f")</td>
        <td class="code">45.200°F</td>
        <td class="code">str</td>
        <td>
            Specified string format used; label from <span class="code"><a href="../options_ref/#Units_Labels">[Units][[Labels]]</a></span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.format("%.3f")</td>
        <td class="code">45.200°F</td>
        <td class="code">str</td>
        <td>
            As above, except a positional argument, instead of the named argument, is being used.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.format(add_label=False)</td>
        <td class="code">45.2</td>
        <td class="code">str</td>
        <td>
            No label. The string formatting is from <span class="code"><a href="../options_ref/#Units_StringFormats">[Units][[StringFormats]]</a></span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.UV</td>
        <td class="code">N/A</td>
        <td class="code">str</td>
        <td>
            The string specified by option <span class="code">NONE</span> in <span class="code"> <a
            href="../options_ref/#Units_StringFormats">[Units][[StringFormats]]</a></span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.UV.format(None_string="No UV")</td>
        <td class="code">No UV</td>
        <td class="code">str</td>
        <td>
            Specified <span class="code">None_string</span> is used.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.windDir</td>
        <td class="code">138&deg;</td>
        <td class="code">str</td>
        <td>
            Formatting is from option <span class="code">degree_compass</span> in <span class="code"> <a
            href="../options_ref/#Units_StringFormats">[Units][[StringFormats]]</a></span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.windDir.ordinal_compass</td>
        <td class="code">SW</td>
        <td class="code">str</td>
        <td>
            Ordinal direction from section <span class="code"><a
            href="../options_ref/#Units_Ordinates">[Units][[Ordinates]]</a></span> is being substituted.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.dateTime</td>
        <td class="code">02-Apr-2010 16:25</td>
        <td class="code">str</td>
        <td>
            Time formatting from <span class="code"><a
            href="../options_ref/#Units_TimeFormats">[Units][[TimeFormats]]</a></span> is being used.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.dateTime.format(format_string="%H:%M")</td>
        <td class="code">16:25</td>
        <td class="code">str</td>
        <td>
            Specified time format used.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.dateTime.format("%H:%M")</td>
        <td class="code">16:25</td>
        <td class="code">str</td>
        <td>
            As above, except a positional argument, instead of the named argument, is being used.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.dateTime.raw</td>
        <td class="code">1270250700</td>
        <td class="code">int</td>
        <td>
            Raw Unix epoch time. The result is an <em>integer</em>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.raw</td>
        <td class="code">45.2</td>
        <td class="code">float</td>
        <td>
            Raw float value. The result is a <em>float</em>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.degree_C.raw</td>
        <td class="code">7.33333333</td>
        <td class="code">float</td>
        <td>
            Raw float value in degrees Celsius. The result is a <em>float</em>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.degree_C.json</td>
        <td class="code">7.33333333</td>
        <td class="code">str</td>
        <td>
            Value in degrees Celsius, converted to a JSON string.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$current.outTemp.degree_C.round(2).json</td>
        <td class="code">7.33</td>
        <td class="code">str</td>
        <td>
            Value in degrees Celsius, rounded to two decimal digits, then converted to a JSON string.
        </td>
    </tr>
    </tbody>
</table>

Note that the same formatting conventions can be used for aggregation periods, such as `$month`, as well as `$current`.

### Start, end, and dateTime

While not an observation type, in many ways the time of an observation, `dateTime`, can be treated as one. A tag such as

    $current.dateTime

represents the _current time_ (more properly, the time as of the end of the last archive interval) and would produce something like

<div class="example_output">
01/09/2010 12:30:00
</div>

Like true observation types, explicit formats can be specified, except that they require a [strftime() _time format_](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) , rather than a _string format_.

For example, adding a format descriptor like this:

    $current.dateTime.format("%d-%b-%Y %H:%M")

produces

<div class="example_output">
09-Jan-2010 12:30
</div>

For _aggregation periods_, such as `$month`, you can request the _start_, _end_, or _length _of the period, by using suffixes `.start`, `.end`, or `.length`, respectively. For example,

    The current month runs from $month.start to $month.end and has $month.length.format("%(day)d %(day_label)s").

results in

<div class="example_output">
The current month runs from 01/01/2010 12:00:00 AM to 02/01/2010 12:00:00 AM and has 31 days.
</div>

The returned string values will always be in _local time_. However, if you ask for the raw value

    $current.dateTime.raw

the returned value will be in Unix Epoch Time (number of seconds since 00:00:00 UTC 1 Jan 1970, _i.e._, a large number), which you must convert yourself. It is guaranteed to never be `None`, so you don't worry have to worry about handling a `None` value.

### Tag $trend

The tag `$trend` is available for time trends, such as changes in barometric pressure. Here are some examples:

| Tag                                  | Results    |
|--------------------------------------|------------|
| `$trend.barometer`                   | -.05 inHg  |
| `$trend($time_delta=3600).barometer` | -.02 inHg  |
| `$trend.outTemp`                     | 1.1 °C     |
| `$trend.time_delta`                  | 10800 secs |
| `$trend.time_delta.hour`             | 3 hrs      |

Note how you can explicitly specify a value in the tag itself (2nd row in the table above). If you do not specify a value, then a default time interval, set by option [time_delta](../options_ref/#trend) in the skin configuration file, will be used. This value can be retrieved by using the syntax `$trend.time_delta` (4th row in the table).

For example, the template expression

    The barometer trend over $trend.time_delta.hour is $trend.barometer.format("%+.2f")

would result in

<div class="example_output">
The barometer trend over 3 hrs is +.03 inHg.
</div>

### Tag `$span`

The tag `$span` allows aggregation over a user defined period up to and including the current time. Its most general form looks like:

```
$span([data_binding=binding_name][,optional_delta=delta][,boundary=[None|'midnight'])
            .obstype
            .aggregation
            [.optional_unit_conversion]
            [.optional_formatting]
```

Where:

_`binding_name`_ is a _binding name_ to a database. An example would be `wx_binding`. See the section _[Binding names](../../custom#binding-names)_ for more details.

_`optional_delta_=delta`_ is one or more comma separated delta settings from the table below. If more than one delta setting is included then the period used for the aggregate is the sum of the individual delta settings. If no delta setting is included, or all included delta settings are zero, the returned aggregate is based on the current obstype only.

_`boundary`_ is an optional specifier that can force the starting time to a time boundary. If set to 'midnight', then the starting time will be at the previous midnight. If left out, then the start time will be the sum of the optional deltas.

_`obstype`_ is a observation type, such as `outTemp`.

_`aggregation`_ is an _aggregation type_. Possible aggregation types are given in _[Appendix: Aggregation types](../appendix/#aggregation_types)_.

_`optional_unit_conversion`_ is an optional unit conversion tag. See the section _[Unit conversion options](#unit-conversion-options)_.

_`optional_formatting`_ is an optional formatting tag that controls how the value will appear. See the section _[Formatting options](#formatting-options)_.

There are several delta settings that can be used:

<table class="indent">
    <tbody>
    <tr class="first_row">
        <td>Delta Setting</td>
        <td>Example</td>
        <td>Meaning</td>
    </tr>
    <tr>
        <td class="first_col code">$time_delta=<em>seconds</em></td>
        <td class="code">$span($time_delta=1800).outTemp.avg</td>
        <td>The average temperature over the last immediate 30 minutes (1800 seconds).
        </td>
    </tr>
    <tr>
        <td class="first_col code">$hour_delta=<em>hours</em></td>
        <td class="code">$span($hour_delta=6).outTemp.avg</td>
        <td>The average temperature over the last immediate 6 hours.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$day_delta=<em>days</em></td>
        <td class="code">$span($day_delta=1).rain.sum</td>
        <td>The total rainfall over the last immediate 24 hours.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$week_delta=<em>weeks</em></td>
        <td class="code">$span($week_delta=2).barometer.max</td>
        <td>The maximum barometric pressure over the last immediate 2 weeks.
        </td>
    </tr>
    </tbody>
</table>

For example, the template expressions

    The total rainfall over the last 30 hours is $span($hour_delta=30).rain.sum

and

    The total rainfall over the last 30 hours is $span($hour_delta=6, $day_delta=1).rain.sum

would both result in

<div class="example_output">
The total rainfall over the last 30 hours is 1.24 in
</div>



### Tag $unit

The type, label, and string formats for all units are also available, allowing you to do highly customized labels:

| Tag                       | Results    |
|---------------------------|------------|
| `$unit.unit_type.outTemp` | `degree_C` |
| `$unit.label.outTemp`     | °C         |
| `$unit.format.outTemp`    | `%.1f`     |

For example, the tag

    $day.outTemp.max.format(add_label=False)$unit.label.outTemp

would result in

<div class="example_output">
21.2°C
</div>

(assuming metric values have been specified for `group_temperature`), essentially reproducing the results of the simpler tag `$day.outTemp.max`.

### Tag $obs

The labels used for the various observation types are available using tag `$obs`. These are basically the values given in the skin dictionary, section [[Labels][[Generic]]](../options_ref/#Labels_Generic).

| Tag                  | Results             |
|----------------------|---------------------|
| `$obs.label.outTemp` | Outside Temperature |
| `$obs.label.UV`      | UV Index            |

### Iteration

It is possible to iterate over the following:

<table class="indent">
    <tbody>
    <tr class="first_row">
        <td>Tag suffix</td>
        <td>Results</td>
    </tr>
    <tr>
        <td class="code first_col">.records</td>
        <td>Iterate over every record</td>
    </tr>
    <tr>
        <td class="code first_col">.hours</td>
        <td>Iterate by hours</td>
    </tr>
    <tr>
        <td class="code first_col">.days</td>
        <td>Iterate by days</td>
    </tr>
    <tr>
        <td class="code first_col">.months</td>
        <td>Iterate by months</td>
    </tr>
    <tr>
        <td class="code first_col">.years</td>
        <td>Iterate by years</td>
    </tr>
    <tr>
        <td class="code first_col">.spans(interval=<em>seconds</em>)
        </td>
        <td>Iterate by custom length spans. The default interval is 10800 seconds (3 hours). The spans will
            align to local time boundaries.
        </td>
    </tr>
    </tbody>
</table>


The following template uses a Cheetah for loop to iterate over all months in a year, printing out each month's min and max temperature. The iteration loop is ==highlighted==.

```hl_lines="2 4"
Min, max temperatures by month
#for $month in $year.months
$month.dateTime.format("%B"): Min, max temperatures: $month.outTemp.min $month.outTemp.max
#end for
```

The result is:

```
Min, max temperatures by month
January: Min, max temperatures: 30.1°F 51.5°F  
February: Min, max temperatures: 24.4°F 58.6°F  
March: Min, max temperatures: 27.3°F 64.1°F  
April: Min, max temperatures: 33.2°F 52.5°F  
May: Min, max temperatures: N/A N/A  
June: Min, max temperatures: N/A N/A  
July: Min, max temperatures: N/A N/A  
August: Min, max temperatures: N/A N/A  
September: Min, max temperatures: N/A N/A  
October: Min, max temperatures: N/A N/A  
November: Min, max temperatures: N/A N/A  
December: Min, max temperatures: N/A N/A
```
The following template again uses a Cheetah `for` loop, this time to iterate over 3-hour spans over the last 24 hours, displaying the averages in each span. The iteration loop is ==highlighted==.

```html hl_lines="6 10"
<p>3 hour averages over the last 24 hours</p>
<table>
  <tr>
    <td>Date/time</td><td>outTemp</td><td>outHumidity</td>
  </tr>
#for $_span in $span($day_delta=1).spans(interval=10800)
  <tr>
    <td>$_span.start.format("%d/%m %H:%M")</td>
    <td>$_span.outTemp.avg</td>
    <td>$_span.outHumidity.avg</td>
  </tr>
#end for
</table>
```

The result is:

<div class="example_output">
    <p>3 hour averages over the last 24 hours</p>
    <table>
        <tr>
            <td>Date/time</td>
            <td>outTemp</td>
            <td>outHumidity</td>
        </tr>
        <tr>
            <td>21/01 18:50</td>
            <td>33.4&#176;F</td>
            <td>95%</td>
        </tr>
        <tr>
            <td>21/01 21:50</td>
            <td>32.8&#176;F</td>
            <td>96%</td>
        </tr>
        <tr>
            <td>22/01 00:50</td>
            <td>33.2&#176;F</td>
            <td>96%</td>
        </tr>
        <tr>
            <td>22/01 03:50</td>
            <td>33.2&#176;F</td>
            <td>96%</td>
        </tr>
        <tr>
            <td>22/01 06:50</td>
            <td>33.8&#176;F</td>
            <td>96%</td>
        </tr>
        <tr>
            <td>22/01 09:50</td>
            <td>36.8&#176;F</td>
            <td>95%</td>
        </tr>
        <tr>
            <td>22/01 12:50</td>
            <td>39.4&#176;F</td>
            <td>91%</td>
        </tr>
        <tr>
            <td>22/01 15:50</td>
            <td>35.4&#176;F</td>
            <td>93%</td>
        </tr>
    </table>

</div>


See the NOAA template files `NOAA/NOAA-YYYY.txt.tmpl` and `NOAA/NOAA-YYYY-MM.txt.tmpl`, both included in the _Seasons_ skin, for other examples using iteration and explicit formatting.

### Comprehensive example

This example is designed to put together a lot of the elements described above, including iteration, aggregation period starts and ends, formatting, and overriding units. [Click here](../examples/tag.htm) for the results.

```html
<html>
  <head>
    <style>
      td { border: 1px solid #cccccc; padding: 5px; }
    </style>
  </head>

  <body>
    <table border=1 style="border-collapse:collapse;">
      <tr style="font-weight:bold">
        <td>Time interval</td>
        <td>Max temperature</td>
        <td>Time</td>
      </tr>
#for $hour in $day($days_ago=1).hours
      <tr>
        <td>$hour.start.format("%H:%M")-$hour.end.format("%H:%M")</td>
        <td>$hour.outTemp.max ($hour.outTemp.max.degree_C)</td>
        <td>$hour.outTemp.maxtime.format("%H:%M")</td>
      </tr>
#end for
      <caption>
        <p>
          Hourly max temperatures yesterday<br/>
          $day($days_ago=1).start.format("%d-%b-%Y")
        </p>
      </caption>
    </table>
  </body>
</html>
```

### Helper functions

WeeWX includes a number of helper functions that may be useful when writing templates.

<table class="indent">
    <caption>Cheetah helper functions</caption>
    <tbody>
    <tr class="first_row">
        <td>Function</td>
        <td>Description</td>
    </tr>
    <tr>
        <td class="first_col code">$rnd(x, ndigits=None)</td>
        <td>
            Round <span class="code">x</span> to <span class="code">ndigits</span> decimal digits. The argument
            <span class="code">x</span> can be a <span class="code">float</span> or a list of <span
            class="code">floats</span>. Values of <span class="code">None</span> are passed through.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$jsonize(seq)</td>
        <td>Convert the iterable <span class="code">seq</span> to a JSON string.</td>
    </tr>
    <tr>
        <td class="first_col code">$to_int(x)</td>
        <td>
            Convert <span class="code">x</span> to an integer. The argument <span class="code">x</span> can be
            of type <span class="code">float</span> or <span class="code">str</span>. Values of <span
            class="code">None</span> are passed through.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$to_bool(x)</td>
        <td>
            Convert <span class="code">x</span> to a boolean.
            The argument <span class="code">x</span> can be
            of type <span class="code">int</span>,
            <span class="code">float</span>, or 
            <span class="code">str</span>.
            If lowercase <span class="code">x</span> is
            'true', 'yes', or 'y' the function returns 
            <span class="code">True</span>. 
            If it is 'false', 'no', or 'n' it returns
            <span class="code">False</span>.
            Other string values raise a 
            <span class="code">ValueError</span>.
            In case of a numeric argument, 0 means 
            <span class="code">False</span>, all other
            values <span class="code">True</span>.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$to_list(x)</td>
        <td>
            Convert <span class="code">x</span> to a list.
            If <span class="code">x</span> is already a list,
            nothing changes. If it is a single value it
            is converted to a list with this value as the
            only list element. Values of <span
            class="code">None</span> are passed through.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$getobs(plot_name)</td>
        <td>
            For a given plot name, this function will return the set of all observation types used by the plot.
            <a href="#getobs-more-info">More information.</a>
        <div id="getobs-more-info" class="modal-dialog">
            <div>
                <a href="#close" title="Close" class="close-dialog">X</a>
                <p>
                    For example, consider a plot that is defined in <span class="code">[ImageGenerator]</span> as
                </p>
                <pre class="tty">
[[[daytempleaf]]]
  [[[[leafTemp1]]]]
  [[[[leafTemp2]]]]
  [[[[temperature]]]]
    data_type = outTemp</pre>
                <p>The tag <span class="code">$getobs('daytempleaf')</span> would return the
                set <span class="code">{'leafTemp1', 'leafTemp2', 'outTemp'}</span>.</p>
            </div>
        </div>
        </td>
    </tr>
    </tbody>
</table>

### Support for series

!!! Note
    This is an experimental API that could change.

WeeWX V4.5 introduced some experimental tags for producing _series_ of data, possibly aggregated. This can be useful for creating the JSON data needed for JavaScript plotting packages, such as [HighCharts](https://www.highcharts.com/), [Google Charts](https://developers.google.com/chart), or [C3.js](https://c3js.org/).

For example, suppose you need the maximum temperature for each day of the month. This tag

    $month.outTemp.series(aggregate_type='max', aggregate_interval='day', time_series='start').json

would produce the following:

    [[1614585600, 58.2], [1614672000, 55.8], [1614758400, 59.6], [1614844800, 57.8], ... ]

This is a list of (time, temperature) for each day of the month, in JSON, easily consumed by many of these plotting packages.

Many other combinations are possible. See the Wiki article [_Tags for series_](https://github.com/weewx/weewx/wiki/Tags-for-series).

### General tags

There are some general tags that do not reflect observation data, but technical information about the template files. They are frequently useful in `#if` expressions to control how Cheetah processes the template.

<table class="indent">
  <tbody>
    <tr class="first_row">
      <td>Tag</td>
      <td>Description</td>
    </tr>
    <tr>
      <td class="code first_col">$encoding</td>
      <td>Character encoding, to which the file is converted
      after creation. Possible values are
      <span class="code">html_entities</span>,
      <span class="code">strict_ascii</span>,
      <span class="code">normalized_ascii</span>, and
      <span class="code">utf-8</span>.
      </td>
    </tr>
    <tr>
      <td class="code first_col">$filename</td>
      <td>
        Name of the file to be created including relative path.
        Can be used to set the canonical URL for search engines.
        <pre class="tty">&lt;link rel="canonical" href="$station.station_url/$filename" /&gt;</pre>
      </td>
    </tr>
    <tr>
        <td class="code first_col">$lang</td>
        <td>Language code set by the <span class="code">lang</span> option for the report. For example,
            <span class="code">fr</span>, or <span class="code">gr</span>.
        </td>
    </tr>
    <tr>
      <td class="code first_col">$month_name</td>
      <td>For templates listed under <span class="code">SummaryByMonth</span>, this will contain the localized
          month name (<em>e.g.</em>, "<em>Sep</em>").</td>
    </tr>
    <tr>
        <td class="code first_col">$page</td>
        <td>The section name from <span class="code">skin.conf</span> where the template is described.</td>
    </tr>
    <tr>
        <td class="code first_col">$skin</td>
        <td>The value of option <span class="code">skin</span> in <span class="code">weewx.conf</span>.</td>
    </tr>
    <tr>
        <td class="code first_col">$SKIN_NAME</td>
        <td>
            All skin included with WeeWX, version 4.6 or later, include the tag
            <span class="code">$SKIN_NAME</span>. For example, for
            the <em>Seasons</em> skin, <span class="code">$SKIN_NAME</span> would return
            <span class="code">Seasons</span>.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$SKIN_VERSION</td>
        <td>
            All skin included with WeeWX, version 4.6 or later, include the tag
            <span class="code">$SKIN_VERSION</span>, which returns the WeeWX version number of when the skin was
            installed. Because skins are not touched during the upgrade process, this shows the origin of the
            skin.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$SummaryByDay</td>
        <td>
            A list of year-month-day strings (<em>e.g.</em>, <span class="code">["2018-12-31", "2019-01-01"]</span>)
            for which a summary-by-day has been generated.
            The <span class="code">[[SummaryByDay]]</span> section must have been processed before this tag
            will be valid, otherwise it will be empty.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$SummaryByMonth</td>
        <td>
            A list of year-month strings (<em>e.g.</em>, <span class="code">["2018-12", "2019-01"]</span>)
            for which a summary-by-month has been generated.
            The <span class="code">[[SummaryByMonth]]</span> section must have been processed before this tag
            will be valid, otherwise it will be empty.
        </td>
    </tr>
    <tr>
        <td class="code first_col">$SummaryByYear</td>
        <td>
            A list of year strings (<em>e.g.</em>, <span class="code">["2018", "2019"]</span>)
            for which a summary-by-year has been generated.
            The <span class="code">[[SummaryByYear]]</span> section must have been processed before this tag
            will be valid, otherwise it will be empty.
        </td>
    </tr>            
    <tr>
      <td class="code first_col">$year_name</td>
        <td>For templates listed under <span class="code">SummaryByMonth</span> or
            <span class="code">SummaryByYear</span>, this will contain the year (<em>e.g.</em>, "2018").</td>
    </tr>
  </tbody>
</table>


### Internationalization support with `$gettext`

Pages generated by WeeWX not only contain observation data, but also static text. The WeeWX tag `$gettext` provides internationalization support for these kinds of texts. It is structured very similarly to the [GNU gettext facility](https://www.gnu.org/software/gettext/), but its implementation is very different. To support internationalization of your template, do not use static text in your templates, but rather use `$gettext`. Here's how.

Suppose you write a skin called "YourSkin", and you want to include a headline labelled "Current Conditions" in English, "aktuelle Werte" in German, "Conditions actuelles" in French, etc. Then the template file could contain:

```
...

<h1>$gettext("Current Conditions")</h1>

...
```

The section of `weewx.conf` configuring your skin would look something like this:

```
...
[StdReport]
    ...
    [[YourSkinReport]]
        skin = YourSkin
        lang = fr
    ...
```

With `lang = fr` the report is in French. To get it in English, replace the language code `fr` by the code for English `en`. And to get it in German use `de`.

To make this all work, a language file has to be created for each supported language. The language files reside in the `lang` subdirectory of the skin directory that is defined by the skin option. The file name of the language file is the language code appended by `.conf`, for example `en.conf`, `de.conf`, or `fr.conf`.

The language file has the same layout as `skin.conf`, _i.e._ you can put language specific versions of the labels there. Additionally, a section `[Texts]` can be defined to hold the static texts used in the skin. For the example above the language files would contain the following:

`en.conf`

```
...
[Texts]
    "Current Conditions" = Current Conditions
    ...
```

`de.conf`

```
...
[Texts]
    "Current Conditions" = Aktuelle Werte
    ...
```

`fr.conf`

```
...
[Texts]
    "Current Conditions" = Conditions actuelles
    ...
```

While it is not technically necessary, we recommend using the whole English text for the key. This makes the template easier to read, and easier for the translator. In the absence of a translation, it will also be the default, so the skin will still be usable, even if a translation is not available.

See the subdirectory `SKIN_ROOT/Seasons/lang` for examples of language files.


#### Context sensitive lookups: `$pgettext()`

A common problem is that the same string may have different translations, depending on its context. For example, in English, the word "Altitude" is used to mean both height above sea level, and the angle of a heavenly body from the horizon, but that's not necessarily true in other languages. For example, in Thai, "ระดับความสูง" is used to mean the former, "อัลติจูด" the latter. The function `pgettext()` (the "p" stands for _particular_) allows you to distinguish between the two. Its semantics are very similar to the [GNU](https://www.gnu.org/software/gettext/manual/gettext.html#Contexts) and [Python](https://docs.python.org/3/library/gettext.html#gettext.pgettext) versions of the function. Here's an example:

```
<p>$pgettext("Geographical","Altitude"): $station.altitude</p>
<p>$pgettext("Astronomical","Altitude"): $almanac.moon.alt</p>
```

The `[Texts]` section of the language file should then contain a subsection for each context. For example, the Thai language file would include:

`th.conf`

```
[Texts]
    ...
    [[Geographical]]
        "Altitude" = "ระดับความสูง"    # As in height above sea level
    [[Astronomical]]
        "Altitude" = "อัลติจูด"         # As in angle above the horizon
    ...
```        

## Almanac

If module [pyephem](https://rhodesmill.org/pyephem) has been installed, then WeeWX can generate extensive almanac information for the Sun, Moon, Venus, Mars, Jupiter, and other heavenly bodies, including their rise, transit and set times, as well as their azimuth and altitude. Other information is also available.

Here is an example template:

```
Current time is $current.dateTime
#if $almanac.hasExtras
    Sunrise, transit, sunset: $almanac.sun.rise $almanac.sun.transit $almanac.sun.set
    Moonrise, transit, moonset: $almanac.moon.rise $almanac.moon.transit $almanac.moon.set
    Mars rise, transit, set: $almanac.mars.rise $almanac.mars.transit $almanac.mars.set
    Azimuth, altitude of mars: $almanac.mars.az $almanac.mars.alt
    Next new, full moon: $almanac.next_new_moon $almanac.next_full_moon
    Next summer, winter solstice: $almanac.next_summer_solstice $almanac.next_winter_solstice
#else
    Sunrise, sunset: $almanac.sunrise $almanac.sunset
#end if
```

If pyephem is installed this would result in:

<div class="example_output">
Current time is 29-Mar-2011 09:20<br/>
Sunrise, transit, sunset: 06:51 13:11 19:30<br/>  
Moonrise, transit, moonset: 04:33 09:44 15:04  <br/>
Mars rise, transit, set: 06:35 12:30 18:26  <br/>
Azimuth, altitude of mars: 124.354959275 26.4808431952<br/>  
Next new, full moon: 03-Apr-2011 07:32 17-Apr-2011 19:43  <br/>
Next summer, winter solstice: 21-Jun-2011 10:16 21-Dec-2011 21:29<br/>
</div>

Otherwise, a fallback of basic calculations is used, resulting in:

<div class="example_output">
Current time is 29-Mar-2011 09:20<br/>  
Sunrise, sunset: 06:51 19:30
</div>

As shown in the example, you can test whether this extended almanac information is available with the value `$almanac.hasExtras`.

The almanac information falls into three categories:

*   Calendar events
*   Heavenly bodies
*   Functions

We will cover each of these separately.

### Calendar events

"Calendar events" do not require a heavenly body. They cover things such as the time of the next solstice or next first quarter moon, or the sidereal time. The syntax is:

    $almanac.next_solstice

or

    $almanac.next_first_quarter_moon

or

    $almanac.sidereal_time

Here is a table of the information that falls into this category:

<table class="indent">
    <caption>Calendar events</caption>
    <tbody class="code">
    <tr>
        <td>previous_equinox</td>
        <td>next_equinox</td>
    </tr>
    <tr>
        <td>previous_solstice</td>
        <td>next_solstice</td>
    </tr>
    <tr>
        <td>previous_autumnal_equinox</td>
        <td>next_autumnal_equinox</td>
    </tr>
    <tr>
        <td>previous_vernal_equinox</td>
        <td>next_vernal_equinox</td>
    </tr>
    <tr>
        <td>previous_winter_solstice</td>
        <td>next_winter_solstice</td>
    </tr>
    <tr>
        <td>previous_summer_solstice</td>
        <td>next_summer_solstice</td>
    </tr>
    <tr>
        <td>previous_new_moon</td>
        <td>next_new_moon</td>
    </tr>
    <tr>
        <td>previous_first_quarter_moon</td>
        <td>next_first_quarter_moon</td>
    </tr>
    <tr>
        <td>previous_full_moon</td>
        <td>next_full_moon</td>
    </tr>
    <tr>
        <td>previous_last_quarter_moon</td>
        <td>next_last_quarter_moon</td>
    </tr>
    <tr>
        <td>sidereal_time</td>
        <td></td>
    </tr>
    <tr>
        <td></td>
        <td></td>
    </tr>
    </tbody>
</table>

!!! Note
    The tag `$almanac.sidereal_time` returns a value in decimal degrees rather than a customary value from 0 to 24 hours.

### Heavenly bodies


The second category does require a heavenly body. This covers queries such as, "When does Jupiter rise?" or, "When does the sun transit?" Examples are

    $almanac.jupiter.rise

or

    $almanac.sun.transit

To accurately calculate these times, WeeWX automatically uses the present temperature and pressure to calculate refraction effects. However, you can override these values, which will be necessary if you wish to match the almanac times published by the Naval Observatory [as explained in the pyephem documentation](https://rhodesmill.org/pyephem/rise-set.html). For example, to match the sunrise time as published by the Observatory, instead of

    $almanac.sun.rise

use

    $almanac(pressure=0, horizon=-34.0/60.0).sun.rise

By setting pressure to zero we are bypassing the refraction calculations
and manually setting the horizon to be 34 arcminutes lower than the
normal horizon. This is what the Navy uses.

If you wish to calculate the start of civil twilight, you can set the
horizon to -6 degrees, and also tell WeeWX to use the center of the sun
(instead of the upper limb, which it normally uses) to do the
calcuation:

    $almanac(pressure=0, horizon=-6).sun(use_center=1).rise

The general syntax is:

``` 
$almanac(almanac_time=time,            ## Unix epoch time
         lat=latitude, lon=longitude,  ## degrees
         altitude=altitude,            ## meters
         pressure=pressure,            ## mbars
         horizon=horizon,              ## degrees
         temperature=temperature_C     ## degrees C
       ).heavenly_body(use_center=[01]).attribute
      
```

As you can see, many other properties can be overridden besides pressure
and the horizon angle.

PyEphem offers an extensive list of objects that can be used for the
_`heavenly_body`_ tag. All the planets and many stars are in the
list.

The possible values for the _`attribute`_ tag are listed in the
following table:

<table class="indent" style="width: 80%">
    <caption>Attributes that can be used with heavenly bodies
    </caption>
    <tbody class="code">
    <tr>
        <td>az</td>
        <td>alt</td>
    </tr>
    <tr>
        <td>a_ra</td>
        <td>a_dec</td>
    </tr>
    <tr>
        <td>g_ra</td>
        <td>ra</td>
    </tr>
    <tr>
        <td>g_dec</td>
        <td>dec</td>
    </tr>
    <tr>
        <td>elong</td>
        <td>radius</td>
    </tr>
    <tr>
        <td>hlong</td>
        <td>hlat</td>
    </tr>
    <tr>
        <td>sublat</td>
        <td>sublong</td>
    </tr>
    <tr>
        <td>next_rising</td>
        <td>next_setting</td>
    </tr>
    <tr>
        <td>next_transit</td>
        <td>next_antitransit</td>
    </tr>
    <tr>
        <td>previous_rising</td>
        <td>previous_setting</td>
    </tr>
    <tr>
        <td>previous_transit</td>
        <td>previous_antitransit</td>
    </tr>
    <tr>
        <td>rise</td>
        <td>set</td>
    </tr>
    <tr>
        <td>transit</td>
        <td>visible</td>
    </tr>
    <tr>
        <td>visible_change</td>
        <td> </td>
    </tr>
    </tbody>
</table>

!!! Note
    The tags `ra`, `a_ra` and `g_ra` return values in decimal degrees rather than customary values from 0 to 24 hours.

### Functions

There is actually one function in this category:
`separation`. It returns the angular separation between two
heavenly bodies. For example, to calculate the angular separation
between Venus and Mars you would use:

``` tty
<p>The separation between Venus and Mars is
      $almanac.separation(($almanac.venus.alt,$almanac.venus.az), ($almanac.mars.alt,$almanac.mars.az))</p>
     
```

This would result in:

<div class="example_output">
The separation between Venus and Mars is 55:55:31.8
</div>

### Adding new bodies to the almanac

It is possible to extend the WeeWX almanac, adding new bodies that it
was not previously aware of. For example, say we wanted to add [*433
Eros*](https://en.wikipedia.org/wiki/433_Eros), the first asteroid
visited by a spacecraft. Here is the process:

1.  Put the following in the file `user/extensions.py`:

    ``` tty
    import ephem
    eros = ephem.readdb("433 Eros,e,10.8276,304.3222,178.8165,1.457940,0.5598795,0.22258902,71.2803,09/04.0/2017,2000,H11.16,0.46")
    ephem.Eros = eros
    ```

    This does two things: it adds orbital information about *433 Eros*
    to the internal pyephem database, and it makes that data available
    under the name `Eros` (note the capital letter).

2.  You can then use *433 Eros* like any other body in your templates.
    For example, to display when it will rise above the horizon:

    ``` tty
    $almanac.eros.rise
    ```

## Wind

Wind deserves a few comments because it is stored in the database in two
different ways: as a set of scalars, and as a *vector* of speed and
direction. Here are the four wind-related scalars stored in the main
archive database:

<table class="indent">
    <tbody>
    <tr class="first_row">
        <td>Archive type</td>
        <td>Meaning</td>
        <td>Valid contexts</td>
    </tr>
    <tr>
        <td class="first_col code">windSpeed</td>
        <td>The average wind speed seen during the archive period.
        </td>
        <td rowspan='4' class='code'>
            $current, $latest, $hour, $day, $week, $month, $year, $rainyear
        </td>
    </tr>
    <tr>
        <td class="first_col code">windDir</td>
        <td>If software record generation is used, this is the vector average over the archive period. If
            hardware record generation is used, the value is hardware dependent.
        </td>
    </tr>
    <tr>
        <td class="first_col code">windGust</td>
        <td>The maximum (gust) wind speed seen during the archive period.
        </td>
    </tr>
    <tr>
        <td class="first_col code">windGustDir</td>
        <td>The direction of the wind when the gust was observed.</td>
    </tr>
    </tbody>
</table>


Some wind aggregation types, notably `vecdir` and `vecavg`, require wind speed *and* direction. For
these, WeeWX provides a composite observation type called `wind`. It is stored directly in the
daily summaries, but synthesized for aggregations other than multiples of a day.

| Daily summary type | Meaning                         |  Valid contexts                                          |
|--------------------|---------------------------------|----------------------------------------------------------|
| wind               | A vector composite of the wind. | `$hour`, `$day`, `$week`, `$month`, `$year`, `$rainyear` |
  
Any of these can be used in your tags. Here are some examples:

<table class="indent">
    <tbody>
    <tr class="first_row">
        <td>Tag</td>
        <td>Meaning</td>
    </tr>
    <tr>
        <td class="first_col code">$current.windSpeed</td>
        <td>The average wind speed over the most recent archive interval.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$current.windDir</td>
        <td>If software record generation is used, this is the vector average over the archive interval. If
            hardware record generation is used, the value is hardware dependent.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$current.windGust</td>
        <td>The maximum wind speed (gust) over the most recent archive interval.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$current.windGustDir</td>
        <td>The direction of the gust.</td>
    </tr>
    <tr>
        <td class="first_col code">$day.windSpeed.avg<br/>$day.wind.avg</td>
        <td>The average wind speed since midnight. If the wind blows east at 5 m/s for 2 hours, then west at 5
            m/s for 2 hours, the average wind speed is 5 m/s.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$day.wind.vecavg</td>
        <td>The <em>vector average</em> wind speed since midnight. If the wind blows east at 5 m/s for 2 hours,
            then west at 5 m/s for 2 hours, the vector average wind speed is zero.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$day.wind.vecdir</td>
        <td>The direction of the vector averaged wind speed. If the wind blows northwest at 5 m/s for two hours,
            then southwest at 5 m/s for two hours, the vector averaged direction is west.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$day.windGust.max<br/>$day.wind.max</td>
        <td>The maximum wind gust since midnight.</td>
    </tr>
    <tr>
        <td class="first_col code">$day.wind.gustdir</td>
        <td>The direction of the maximum wind gust.</td>
    </tr>
    <tr>
        <td class="first_col code">$day.windGust.maxtime<br/>$day.wind.maxtime</td>
        <td>The time of the maximum wind gust.</td>
    </tr>
    <tr>
        <td class="first_col code">$day.windSpeed.max</td>
        <td>The max average wind speed. The wind is averaged over each of the archive intervals. Then the
            maximum of these values is taken. Note that this is <em>not</em> the same as the maximum wind gust.
        </td>
    </tr>
    <tr>
        <td class="first_col code">$day.windDir.avg</td>
        <td>
            Not a very useful quantity. This is the strict, arithmetic average of all the compass wind
            directions. If the wind blows at 350&deg; for two hours then at 10&deg; for two hours,
            then the scalar average wind direction will be 180&deg; &mdash; probably not what you
            expect, nor want.
        </td>
    </tr>
    </tbody>
</table>


## Defining new tags {#defining_new_tags}

We have seen how you can change a template and make use of the various tags available such as
`$day.outTemp.max` for the maximum outside temperature for the day. But, what if you want to
introduce some new data for which no tag is available?

If you wish to introduce a static tag, that is, one that will not change with time (such as a
Google Analytics tracker ID, or your name), then this is very easy: simply put it in section
[`[Extras]`](#Extras) in the skin configuration file. More information on how to do this can be found
there.

But, what if you wish to introduce a more dynamic tag, one that requires some calculation, or
perhaps uses the database? Simply putting it in the `[Extras]` section won't do, because then it
cannot change.

The answer is to write a *search list extension*. Complete directioins on how to do this are in a
companion document [*Writing search list extensions*](/sle).

