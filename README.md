# 🚀 SwitchMQ Message Broker (Final)

A lightweight, fast, and scalable **message broker**, built from scratch — inspired by RabbitMQ but designed for modern distributed systems. This is the **MVP-1**, developed in a focused one-week solo sprint.

## ⚙️ What It Is

This is a custom-built message broker that handles message queuing and delivery between producers and consumers. It's designed to be:

- ⚡ **High-performance**: Low-latency and optimized for throughput  
- 🧵 **Lightweight**: Minimal overhead, focused core features  
- 🧱 **Scalable**: Horizontal scaling is a core consideration  
- 🛠️ **Hackable**: Built from scratch and easy to understand  

> ⚠️ This is an MVP and not yet production-ready — but a solid foundation to build on.

## ✨ Features (MVP-2)

- [x] Basic message queues  
- [x] Pub/sub model support  
- [x] In-memory message storage  
- [x] Back-pressure handling  
- [x] Message Persistence (Exchange-Level)
- [x] Monitoring 
- [ ] Clustering (coming soon)

## 🧭 Project Roadmap

- 🚀 Migrate to Rust or Go
- 🌐 Native clustering support
- 💾 Full message persistence
- 🔐 Security layers (encryption)
- 📊 Real-time dashboard & metrics

## Steps to Install & Run
1. Clone the repository git clone `https://github.com/harsha-0907/MessageBroker-Server.git`
2. Change directory to the repository `cd MessageBroker-Server`
3. Create Virtual Environment `python3 -m venv .venv`
4. Activate the virtual environment: \
    a. For Linux `source .venv/bin/activate` \
    b. For Windows `..venv\Scripts\activate` 
5. Install the necessary packages using `pip install -r requirments.txt`
6. Open 2 terminals and go to `mbserver` - `cd mbserver` \
    a. Run the utility server using `uvicorn utilServer:app ` \
    b. Run the MessageBroker using `uvicorn mbhandler:app `

                                    
Live Host :- http://switchmq.ddns.net:42425/
Architecture/Documentation :- https://tinyurl.com/switchmq-docs

## ☕ Built With
- 🐍 Python + FastAPI
- 🔄 Asyncio
- 🧪 Uvicorn

Fueled by 🥤 Red Bull, running on async and vibes ❤️
