import torch

print('cuda available: ', torch.cuda.is_available())
print('cuda version: ', torch.version.cuda)
print('gpu count: ', torch.cuda.device_count())