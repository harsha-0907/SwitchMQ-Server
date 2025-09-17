
import asyncio
from exchangeHandler import Exchange

def start_exchange(args):
    hostName=args["hostName"]
    exchangeName=args["exchangeName"]
    port=args["port"]
    queues=args["queues"]
    terminateSwitch=args["terminateSwitch"]
    maxMessages = args["maxMessagesPerExchange"]

    exchange = Exchange(hostName=hostName, exchangeName=exchangeName, port=port, queues=queues, terminateSwitch=terminateSwitch, maxMessages=maxMessages)
    asyncio.run(exchange.handleSocket())  # Runs the async socket server

async def stopExchange(exchangeName, exchanges):
    if exchangeName not in exchanges:
        return True

    print("Terminating Exchange :", exchangeName)

    exchangeObject, exchangeTerminateSwitch = exchanges[exchangeName]
    exchangeTerminateSwitch.set()
    exchangeObject.kill()
    exchangeObject.join(timeout=1)

    if exchangeObject.is_alive():
        print("Process is still alive")
        exchangeObject.kill()
        exchangeObject.join()

    del(exchanges[exchangeName])
    return True



