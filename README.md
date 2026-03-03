# Winglet-BG95

An implementation of the [winglet](https://github.com/TL-Embedded/Winglet-Carrier/blob/main/winglet-modem.md) form factor using the BG95 modem.

By fitting the components for reset control, this should also be compatible as a BG96 modem carrier.

Note that the logic translators are disabled when the modem is off, or in PSM mode. Output should only be driven high if the DCD output is high.