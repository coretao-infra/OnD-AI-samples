# create the simplest of python scripts that takes a normalized prompt (via config)
# targets different LLM models using a canonical helper
# helper uses configurations (json) to set it up to be able to hit different back ends
# intially we will only target different models and variants using Foundry Local
# python script runs on a loop so that it shows an easy to use, menu-driven UI
# records the back end, request token count, response token count, response time, model, variant, timestamp
# this can later be averaged/summarized to compare 
