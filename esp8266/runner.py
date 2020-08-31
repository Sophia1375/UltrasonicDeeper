import gc
import machine
import utime
import uasyncio as asyncio
import ujson
import sensor

deep_sleep_count = 0
deep_sleep_time = 600
ds_temperature = 0


@asyncio.coroutine
async def blink():
    led = machine.Pin(2, machine.Pin.OUT);
    while True:
        led.on()
        await asyncio.sleep_ms(500)
        led.off()
        await asyncio.sleep_ms(500)
        increase()
        # print('deep_sleep=' + str(deep_sleep_count) + ' depth= ' + str(sensor.measure_depth()) + 'voltage=' + str(
        #     sensor.battery_level()))


@asyncio.coroutine
def serve(reader, writer):
    print(reader, writer)
    print("================")
    print((yield from reader.read()))
    yield from writer.awrite("""HTTP/1.0 200 OK\r\n""")
    yield from writer.awrite("""Content-Type: application/json\r\n\r\n""")
    yield from writer.awrite(response())
    print("After response write")
    yield from writer.aclose()
    print("Finished processing request")
    print("deep_sleep= " + str(reset()))
    gc.collect()


@asyncio.coroutine
async def temperature():
    while True:
        try:
            sensor.ds_sensor.convert_temp()
            await asyncio.sleep_ms(750)
            global ds_temperature
            ds_temperature = sensor.ds_sensor.read_temp(sensor.roms[0])
            print('temperature= ' + str(ds_temperature))
            await asyncio.sleep(10)
        except Exception as err:
            print(err)


def increase():
    global deep_sleep_count
    deep_sleep_count += 1
    print("I am going to sleep in " + str(deep_sleep_time - deep_sleep_count))
    if deep_sleep_count > deep_sleep_time:
        print('I am going to sleep')
        machine.deepsleep(0)
    return deep_sleep_count


def reset():
    global deep_sleep_count
    deep_sleep_count = 0
    return deep_sleep_count


def response():
    depths = []
    isSuccess = True
    for iter in range(3):
        measure = sensor.measure_depth()
        if measure > 0:
            depths.append(measure)
    if len(depths) > 1:
        depths.sort()
        if depths[len(depths) - 1] - depths[0] > 1:
            isSuccess = False
    else:
        isSuccess = False
    if isSuccess:
        dict = {"status": 200, "depth": str(depths[0]), "battery": sensor.battery_level(),
                "temperature": str(ds_temperature)}
    else:
        dict = {"status": 300, "depth": "-1", "battery": sensor.battery_level(),
                "temperature": str(ds_temperature)}
    return ujson.dumps(dict)


def run():
    loop = asyncio.get_event_loop()
    loop.call_soon(asyncio.start_server(serve, host="0.0.0.0", port=80))
    loop.create_task(blink())
    loop.create_task(temperature())
    try:
        loop.run_forever()
    except Exception as err:
        loop.close()
        raise err