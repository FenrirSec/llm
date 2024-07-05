#!/usr/bin/env python3

import ollama

DEBUG = True
MAX_RETRIES = 5
QUESTIONS_FILE="questions.csv"
history = []

def parse_questions():
    questions = []
    with open(QUESTIONS_FILE) as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace('"', '')
            splat = line.split(',')
            right_answer = (int(splat[17]) - 1) if len(splat[17]) else None
            if right_answer is not None:
                questions.append({
                    "contents": splat[0],
                    "answers": splat[2:16],
                    "right_answer": right_answer
                })
            else:
                if DEBUG:
                    print('WARNING: Question could not be parsed : ', line)
    return questions

def rephrase(question):
    output = ollama.generate(
        model="phi3",
        prompt=f"Contextualize the following question to give it a bit more context (without giving its answer OR changing its meaning/intention). Do NOT ask the user to give more details or a detailed explanation. DO NOT ANSWER THE QUESTION. The question you have to rephrase is : {question}"
    )
    return output['response']

def main():
    go = True
    question = 0
    while go:
        questions = parse_questions()
        if DEBUG:
            print(f"{questions[question]}")
        q = rephrase(questions[question].get('contents'))
        print(f"Question {question + 1}: {q}")
        history = [{"role": "assistant", "content": q}]
        answer = input(">> ")
        if 'rephrase' in answer.lower():
            continue
        history.append({"role": "user", "content": answer})
        if questions[question].get('right_answer'):
            right_answer = questions[question]['answers'][questions[question].get('right_answer')]
            status = None
            retries = 0
            while status is None:
                if retries > MAX_RETRIES:
                    raise Exception('Max retries exceeded')
                prompt = f"Is this answer : '{answer}' to this question '{q}' true? The ONLY answer you can accept {right_answer}. ANSWER YES ONLY IF THE GIVEN ANSWER IS {right_answer}. OTHERWISE ANSWER 'NO'. DO NOT ACCEPT ANSWERS WITH MULTIPLE ANSWERS. ACCEPT NO ANSWER CONTAINING MULTIPLE ANSWERS. Answer ONLY with 'YES' or 'NO'. NOTHING ELSE. DO NOT EXPLAIN."
                prompt = f"Is the sentence '{answer}' the same as the right answer : '{right_answer}' to the question '{q}'? The ONLY RIGHT ANSWER YOU CAN ACCEPT is '{right_answer}' ANSWER 'YES' IF THE GIVEN SENTENCE IS THE SAME, OTHERWISE ANSWER 'NO'!!! ONLY ANSWER WITH 'YES' OR 'NO', ABSOLUTELY NOTHING ELSE!"
                output = ollama.generate(
                    model="phi3",
                    prompt=prompt
                )
                if output['response'].replace("'", '').strip().replace('.', '') == 'YES':
                    print('Your answer is CORRECT!')
                    status = 'correct'
                elif output['response'].replace("'", '').strip().replace('.', '') == 'NO':
                    print('Your answer is INCORRECT!')
                    status = 'incorrect'
                elif DEBUG:
                    print('INVALID OUTPUT GIVEN BY LLM : ', output['response'])
            output = ollama.generate(
                model="phi3",
                prompt=f"In one short sentence, explain why this answer : {answer} to the question '{q}' is {status} and why the correct response was {right_answer}."
            )
            print(output['response'])
        print('---')
        question += 1
    return 0

if __name__ == "__main__":
    exit(main())
