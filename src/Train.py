import torch
import torch.nn as nn
import torch.optim as optim
import torch.optim.lr_scheduler as lr_scheduler

import os
import mlflow
import mlflow.pytorch
from  mlflow.models.signature import infer_signature
from mlflow.exceptions import MlflowException


from src.Dataset import build_dataloaders
from src.LSTMModel import LSTMModel

def train_model(model, dataset, dataloader, criterion, optimizer):
    size = len(dataset)
    model.train()
    for batch,(X_batch, Y_batch) in enumerate(dataloader):
        optimizer.zero_grad()
        output = model(X_batch)
        #print(f"Outputs shape: {output.shape}, Y_batch shape: {Y_batch.shape}")  # 디버깅용 출력

        loss = criterion(output, Y_batch)
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X_batch)
            print(f"Loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

def test_model(model, dataset, dataloader, loss_fn):
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X_batch, Y_batch in dataloader:
            pred = model(X_batch)
            test_loss += loss_fn(pred, Y_batch).item()
            correct += (pred.argmax(dim=1) == Y_batch).type(torch.float).sum().item()
    
    test_loss /= len(dataloader)
    correct /= len(dataset)
    test_acc = correct * 100.0

    print(f"Test error: \n Accuracy: {(test_acc):>0.1f}%, Avg loss: {test_loss:>8f} \n")

    return test_acc, test_loss


# def run_training(dataset, epochs=10, learning_rate=1e-2, batch_size=64):    
#     train_dataset, test_dataset, train_loader, test_loader = build_dataloaders(dataset, batch_size=64)
    
#     model = LSTMModel(num_embeddings=len(train_dataset.dataset.BOM))

#     loss_fn = nn.CrossEntropyLoss()
#     optimizer = optim.SGD(model.parameters(), lr=learning_rate)
#     scheduler = lr_scheduler.StepLR(optimizer, step_size=epochs, gamma=0.1)

#     best_acc = 0.0

#     with mlflow.start_run() as run:
#         mlflow.log_param("epochs", epochs)
#         mlflow.log_param("learning_rate", learning_rate)
#         mlflow.log_param("batch_size", batch_size)

#         for epoch in range(epochs):
#             print(f"Epoch {epoch+1}\n--------------------------")
#             train_model(model, train_dataset, train_loader, loss_fn, optimizer)
#             test_acc, test_loss = test_model(model, test_dataset, test_loader, loss_fn)

#             mlflow.log_metric('test_acc', test_acc, step=epoch)
#             mlflow.log_metric('test_loss', test_loss, step=epoch)

#             if test_acc > best_acc:
#                 best_acc = test_acc
#                 print(f'new best accuracy : {best_acc}')
#                 mlflow.log_metric('best_acc', best_acc, step=epoch)

#             scheduler.step()
            
#         # `train_dataset[0][0]`을 PyTorch 텐서로 변환
#         input_tensor = torch.tensor(train_dataset[0][0]).unsqueeze(0)
#         model_output = model(torch.tensor(train_dataset[0][0]).unsqueeze(0)).detach().cpu().numpy()

#         # signature = infer_signature(input_tensor, model(input_tensor))
#         signature = infer_signature(input_tensor, model_output)

#         #모델 저장
#         mlflow.pytorch.log_model(model.cpu(), "model", signature=signature, code_paths=['src/LSTMModel.py'])

#         #모델 저장 확인
#         artifact_uri = mlflow.get_artifact_uri("model")
#         if os.path.exists(artifact_uri):
#             print(f"Model successfully saved to {artifact_uri}")
#         else:
#             print(f"Model saving failed at {artifact_uri}")

        
#         model_uri = f"runs:/{run.info.run_id}/model"
#         model_name = "LSTMModel"

#         try:
#             mlflow.register_model(model_uri=model_uri, name=model_name)
#             print(f"Model registered as '{model_name}' in model registry.")
#         except MlflowException as e:
#             print(f"Model registration failed: {e}")
                
#         print("Done!")

import torch
import os
import mlflow
from mlflow.models.signature import infer_signature

def run_training(dataset, epochs=10, learning_rate=1e-2, batch_size=64):    
    train_dataset, test_dataset, train_loader, test_loader = build_dataloaders(dataset, batch_size=batch_size)
    
    model = LSTMModel(num_embeddings=len(train_dataset.dataset.BOM))

    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=learning_rate)
    scheduler = lr_scheduler.StepLR(optimizer, step_size=epochs, gamma=0.1)

    best_acc = 0.0

    with mlflow.start_run() as run:
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("batch_size", batch_size)

        for epoch in range(epochs):
            print(f"Epoch {epoch+1}\n--------------------------")
            train_model(model, train_dataset, train_loader, loss_fn, optimizer)
            test_acc, test_loss = test_model(model, test_dataset, test_loader, loss_fn)

            mlflow.log_metric('test_acc', test_acc, step=epoch)
            mlflow.log_metric('test_loss', test_loss, step=epoch)

            if test_acc > best_acc:
                best_acc = test_acc
                print(f'new best accuracy : {best_acc}')
                mlflow.log_metric('best_acc', best_acc, step=epoch)

            scheduler.step()
        
        # PyTorch 텐서를 numpy로 변환하여 signature 추론
        input_tensor = torch.tensor(train_dataset[0][0]).unsqueeze(0).detach().cpu().numpy()
        model_output = model(torch.tensor(train_dataset[0][0]).unsqueeze(0)).detach().cpu().numpy()

        # 모델의 input/output signature 추론
        signature = infer_signature(input_tensor, model_output)

        # 모델 저장
        mlflow.pytorch.log_model(model.cpu(), "model", signature=signature, code_paths=['src/LSTMModel.py'])

        # 모델 URI 확인
        model_uri = f"runs:/{run.info.run_id}/model"
        print(f"Model successfully logged at {model_uri}")

        # 모델 레지스트리에 모델 등록
        model_name = "LSTMModel"
        try:
            mlflow.register_model(model_uri=model_uri, name=model_name)
            print(f"Model registered as '{model_name}' in model registry.")
        except MlflowException as e:
            print(f"Model registration failed: {e}")

        print("Done!")
        mlflow.end_run()
