from winglet import carrier
import gauntlet
import time
import serial
import re

def command(port, text: str, fmt: str = None, timeout: float = 1.0) -> list[str]:
    send_command(port, text)
    if fmt != None:
        reply = await_reply(port, fmt, timeout)
    else:
        reply = None
    await_reply(port, "OK", timeout)
    return reply

def send_command(port, text: str):
    txt = "AT" + text + "\r\n"
    port.write(txt.encode())

def await_reply(port, fmt: str, timeout: float = 1.0) -> str:
    end = time.time() + timeout
    while 1:
        if time.time() > end:
            raise TimeoutError()
        line = port.readline().decode()
        if line == "":
            continue
        line = line.strip()
        if line.startswith("+CME"):
            raise gauntlet.StepError(line)
        m = re.match(fmt, line)
        if m != None:
            return line

def main():
    dev = carrier.Carrier()
    dev.is_present(True)
    dev.reset()

    port = serial.Serial(dev.find_uart(1), timeout=1.0)
    
    with gauntlet.Gauntlet("EG800Q") as runner:

        runner.step("Power up modem").operation(lambda: dev.set_power(True)).run()
        time.sleep(1.0)
        runner.step("Detect EEPROM").operation(lambda: dev.detect_eeprom()).run()
        runner.step("Write EEPROM").operation(lambda: dev.write_eeprom("EG800Q")).run()
        runner.step("Read EEPROM").measure(lambda: dev.read_eeprom()).equals("EG800Q").run()
        runner.step("Enable uart").operation(lambda: dev.enable_uart(1, True, 115200)).run()

        def step_wake_modem():
            dev.set_wake(True)
            time.sleep(0.5)
            dev.set_wake(False)

        runner.step("Wake modem").operation(step_wake_modem).run()
        runner.step("Await ready").measure( lambda: await_reply(port, r"RDY", timeout=12.0) ).equals("RDY").run()
        runner.step("Echo off").operation( lambda: command(port, "E0") ).run()
        runner.step("Get model").measure( lambda: command(port, "+GMM", ".+")).equals("EG800Q-EU").run()
        runner.step("Get IMEI").measure( lambda: command(port, "+GSN", r"\d+")).run()
        time.sleep(0.5)
        runner.step("Check sim").measure( lambda: command(port, "+CPIN?", r"\+CPIN: .+") ).equals("+CPIN: READY").run()

        def await_registration() -> int:
            for i in range(20):
                reply = command(port, "+CEREG?", r"\+CEREG: 0,")
                status = int(re.match(r"\+CEREG: 0,(\d+)", reply).groups()[0])
                if status != 2:
                    return status
                time.sleep(1.0)
            return status

        runner.step("Connect").measure(await_registration).equals(1).run()
        runner.step("Get IP").measure( lambda: command(port, "+CGPADDR=1", r"\+CGPADDR: 1,") ).run()

        dev.reset()

    port.close()
    dev.close()

if __name__ == "__main__":
    main()