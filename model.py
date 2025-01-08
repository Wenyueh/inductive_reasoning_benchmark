import anthropic
import time, os
from openai import OpenAI
from together import Together


def call_model(args, text):
    if 'wen' in args.model or 'lama' in args.model:
        client = Together(api_key=os.environ['TOGETHER_AI_API'])
        output = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": text}],
            stream=False,
            max_tokens=2000,
        )
        return output.choices[0].message.content
    elif 'sonnet' in args.model:
        api_client = anthropic.Anthropic(
                api_key=os.environ['CLAUDE_AI_API'],
            )
        system_prompt = system_prompt
        message = api_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )
        return message.content[0].text
    elif 'opus' in args.model:
        api_client = anthropic.Anthropic(
                api_key=os.environ['CLAUDE_AI_API'],
            )
        system_prompt = system_prompt
        message = api_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )
        return message.content[0].text
    elif 'gpt-4o' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    elif 'gpt-4o-mini' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    elif 'o1' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "o1-preview", 
            messages=[
                {"role": "user", "content": message},
            ]
            )
        return response.choices[0].message.content
    elif 'sonnet3' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "claude-3-sonnet-20240229", 
            messages=[
                {"role": "user", "content": message},
            ],
            temperature=0.2,
            )
        return response.choices[0].message.content
