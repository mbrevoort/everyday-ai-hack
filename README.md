# Experiments with Email and OpenAI

### Setup 
Define `.env` with these values:

```
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
REDIRECT_URI=https://everydayai.brevoort.com/connect-gmail
```

### Deploying
First you need to login to AWS by running `aws configure`. Choose `us-east-2` for the region.

Deploy with `make deploy`