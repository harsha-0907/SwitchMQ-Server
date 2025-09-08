# 🚀 SwitchMQ Message Broker (MVP-1)

A lightweight, fast, and scalable **message broker**, built from scratch — inspired by RabbitMQ but designed for modern distributed systems. This is the **MVP-1**, developed in a focused one-week solo sprint.

## ⚙️ What It Is

This is a custom-built message broker that handles message queuing and delivery between producers and consumers. It's designed to be:

- ⚡ **High-performance**: Low-latency and optimized for throughput  
- 🧵 **Lightweight**: Minimal overhead, focused core features  
- 🧱 **Scalable**: Horizontal scaling is a core consideration  
- 🛠️ **Hackable**: Built from scratch and easy to understand  

> ⚠️ This is an MVP and not yet production-ready — but a solid foundation to build on.

## ✨ Features (MVP-1)

- [x] Basic message queues  
- [x] Pub/sub model support  
- [x] In-memory message storage  
- [x] Back-pressure handling  
- [ ] Persistence (coming soon)  
- [ ] Monitoring / metrics (coming soon)  
- [ ] Clustering (coming soon)  

## Endpoints
1. Admin-UI/Auth/Other - (PORT - 42425)
2. Message-Broker - (PORT - 42426)
3. Default Exchange - (PORT - 48001)

## Steps to Install & Run
1. Clone the repository git clone `https://github.com/harsha-0907/MessageBroker-Server.git`
2. Change directory to the repository `cd MessageBroker-Server`
3. Create Virtual Environment `python3 -m venv .venv`
4. Activate the virtual environment: \
    a. For Linux `source .venv/bin/activate` \
    b. For Windows `..venv\Scripts\activate` 
5. Install the necessary packages using `pip install -r requirments.txt`
6. Open 2 terminals and go to `mbserver` - `cd mbserver` \
    a. Run the util server using `python3 utilServer.py` \
    b. Run the MessageBroker using `python3 mbserver.py`

                                    



 Now the server is ready to take messages..!

