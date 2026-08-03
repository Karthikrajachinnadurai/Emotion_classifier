import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from utils import load_model_and_tokenizer, predict_emotion, get_cbt_response, load_cbt_responses

print('Loading model...')
model, tokenizer, label_encoder = load_model_and_tokenizer()
cbt = load_cbt_responses()
print('Model loaded OK')

result = predict_emotion('I am feeling very lonely today.', model, tokenizer, label_encoder)
print('Predicted emotion :', result['predicted_emotion'])
print('Confidence        :', f"{result['confidence']*100:.2f}%")
print('Inference time    :', f"{result['inference_time_ms']:.0f} ms")
print('Probabilities:')
for k, v in result['probabilities'].items():
    print(f"  {k}: {v*100:.2f}%")
cbt_resp = get_cbt_response(result['predicted_emotion'], cbt)
print('CBT Response      :', cbt_resp[:100])
print('ALL TESTS PASSED')
