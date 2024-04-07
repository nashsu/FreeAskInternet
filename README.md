# FreeAskInternet


> Running www.perplexity.ai like app complete FREE, LOCAL, PRIVATE and NO GPU NEED on any computer


> [!IMPORTANT]  
> **If you are unable to use this project normally, it is most likely due to issues with your internet connection or your IP, you need free internet connection to use this project normally. 如果您无法正常使用此项目，很可能是由于您的 IP 存在问题，或者你不能自由访问互联网。**

## What is FreeAskInternet
FreeAskInternet is a completely free, private and locally running search aggregator & answer generate using LLM, Without GPU needed. The user can ask a question and the system will use searxng to make a multi engine search and combine the search result to the ChatGPT3.5 LLM and generate the answer based on search results. All process running locally and  No GPU or OpenAI or Google API keys are needed.



## Features 

- 🈚️ Completely FREE (no need for any API keys)
- 💻 Completely LOCAL (no GPU need, any computer can run )
- 🔐 Completely PRIVATE (all thing runing locally)
- 👻 Runs WITHOUT LLM Hardware (NO GPU NEED!)
- 🤩 Using Free ChatGPT3.5 API (NO API keys need! Thx OpenAI)
- 🚀 Fast and easy to deploy with Docker Compose
- 🌐 Web and Mobile friendly interface, allowing for easy access from any device ( Thx ChatGPT-Next-Web )

## How It Works? 

1. System get user input question in ChatGPT-Next-Web ( running locally), and call searxng (running locally) to make search on multi search engine.
2. crawl search result links content and pass to ChatGPT3.5 (using OpenAI ChatGPT3.5, through FreeGPT35 running locally), ask ChatGPT3.5 to answer user question based on this contents as references.
3. Stream the answer to ChatGPT-Next-Web Chat UI.

## Status 

This project is still in its very early days. Expect some bugs. 


### Run the latest release

```bash
git clone https://github.com/nashsu/FreeAskInternet.git
cd ./FreeAskInternet
docker-compose up -d 
```

🎉 You should now be able to open the web interface on http://localhost:3000. Nothing else is exposed by default.


### How to update to latest 

```bash
cd ./FreeAskInternet
git pull
docker compose rm backend
docker image rm nashsu/free_ask_internet
docker-compose up -d
```
 


## Credits
- ChatGPT-Next-Web : [https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web)
- FreeGPT35: [https://github.com/missuo/FreeGPT35](https://github.com/missuo/FreeGPT35)
- searxng: [https://github.com/searxng/searxng](https://github.com/searxng/searxng)

## License
Apache-2.0 license

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=nashsu/FreeAskInternet&type=Date)](https://star-history.com/#nashsu/FreeAskInternet&Date)
