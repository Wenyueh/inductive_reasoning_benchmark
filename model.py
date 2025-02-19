import anthropic
import time, os
from openai import OpenAI
from together import Together


def call_model(args, text):
    if 'wen' in args.model or 'lama' in args.model or 'deepseek' in args.model or 'mistral' in args.model:
        client = Together(api_key=os.environ['TOGETHER_AI_API'])
        if 'R1' in args.model:
            output = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": text}],
                steam=True,
            )
        else:
            output = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": text}],
                steam=False,
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
            messages=[{"role": "user", "content": text}],
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
            messages=[{"role": "user", "content": text}],
        )
        return message.content[0].text
    elif 'gpt-4o' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    elif 'o1-mini' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "o1-mini", 
            messages=[
                {"role": "user", "content": text},
            ]
            )
        return response.choices[0].message.content
    elif 'o3-mini' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "o3-mini", 
            messages=[
                {"role": "user", "content": text},
            ]
            )
        return response.choices[0].message.content
    elif 'o1' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "o1-preview", 
            messages=[
                {"role": "user", "content": text},
            ]
            )
        return response.choices[0].message.content
    elif 'sonnet3' in args.model:
        openai_client = OpenAI(api_key=os.environ['OPENAI_AI_API'])
        response = openai_client.chat.completions.create(
            model = "claude-3-sonnet-20240229", 
            messages=[
                {"role": "user", "content": text},
            ],
            temperature=0.2,
            )
        return response.choices[0].message.content
    
