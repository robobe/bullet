# MSP throughput test

From the repository root, with the workspace Python environment:

```sh
.venv/bin/python tools/msp_stress.py --output /tmp/msp-stress.csv
```

Defaults: `/dev/ttyACM1`, 115200 host baud, 600 seconds. Close other applications
using the port. `--device`, `--baudrate`, and `--duration` override these defaults.
The CSV must not already exist.

The script uses `msp_link` framing and serial transport to continuously poll
MSP_ATTITUDE (108) and MSP_ALTITUDE (109), with one outstanding request per type.
It bypasses the client's synchronous request queue to measure achieved paired
polling throughput without thread handoff delays. This is a measured throughput
for this request pattern, not a proof of the firmware's absolute maximum.

Each line gives validated replies per elapsed second for each type separately.
The summary includes average rate, minimum/maximum full-interval rate, and how
many full intervals fell below 50 Hz. The final partial interval is in the CSV
and average, but excluded from the full-interval threshold check. Exit status is
0 for passing, 1 for a rate failure (or no full interval), 2 for an incomplete run,
and 130 for interruption. Missing replies time out after 300 ms and abort the run.

Native Betaflight USB VCP does not use the configured UART baud to set USB speed.
`--baudrate` sets the host port only; this test writes no firmware settings and
sends no RC commands. Reply frequency does not establish sensor update frequency
or altitude validity: MSP replies contain no sensor timestamps, and an altitude
reply alone does not establish that a working altitude sensor is installed.

If combined throughput is around 100 replies/s, inspect Betaflight's
`serial_update_rate_hz` setting (documented default: 100 Hz). This firmware task
rate is separate from UART baud rate. The script deliberately leaves it unchanged.
See the [Betaflight CLI reference](https://betaflight.com/docs/wiki/guides/current/Cli)
and [STM32 USB VCP driver](https://github.com/betaflight/betaflight/blob/master/src/platform/STM32/serial_usb_vcp.c).

Test without hardware:

```sh
.venv/bin/python -m pytest tools/tests/test_msp_stress.py
```
