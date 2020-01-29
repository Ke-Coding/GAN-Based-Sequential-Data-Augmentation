import torch
import torch.utils.data as data
import torch.nn as nn
import torch.nn.functional as F
import torchvision as tv
import numpy as np
import matplotlib.pyplot as plt
from torchvision import transforms, datasets
from torchvision.transforms import ToPILImage
from torch.autograd import Variable
from torch import optim
import os
import datetime
from torchsummary import summary

mnist_mean = 0.1307
mnist_std = 0.3081
epoch_n = 6

using_gpu = torch.cuda.is_available()


class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()

        channels = [16, 32, 64, 96]
        strides = [1, 2, 1]
        ex_ch = [ch * 3 for ch in channels]

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, channels[0], kernel_size=3, padding=1, stride=2, bias=False),
            nn.BatchNorm2d(channels[0]),
            nn.ReLU6()
        )

        # Bottleneck第一层和第三层都是pointwise卷积，也即kernel_size=1，groups=1的卷积，
        # 第二层是depthwise卷积，也即kernel_size=3，groups=channels的卷积
        self.bottleneck1 = nn.Sequential(
            nn.Conv2d(channels[0], ex_ch[0], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(ex_ch[0]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[0], ex_ch[0], kernel_size=3, padding=1, stride=strides[0], groups=ex_ch[0], bias=False),
            nn.BatchNorm2d(ex_ch[0]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[0], channels[1], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(channels[1])
        )
        self.bottleneck2 = nn.Sequential(
            nn.Conv2d(channels[1], ex_ch[1], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(ex_ch[1]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[1], ex_ch[1], kernel_size=3, padding=1, stride=strides[1], groups=ex_ch[1], bias=False),
            nn.BatchNorm2d(ex_ch[1]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[1], channels[2], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(channels[2])
        )
        self.bottleneck3 = nn.Sequential(
            nn.Conv2d(channels[2], ex_ch[2], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(ex_ch[2]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[2], ex_ch[2], kernel_size=3, padding=1, stride=strides[2], groups=ex_ch[2], bias=False),
            nn.BatchNorm2d(ex_ch[2]),
            nn.ReLU6(),
            nn.Conv2d(ex_ch[2], channels[3], kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(channels[3])
        )

        self.last_ch = 144
        self.conv2 = nn.Sequential(
            nn.Conv2d(channels[-1], self.last_ch, kernel_size=1, padding=0, stride=1, bias=False),
            nn.BatchNorm2d(self.last_ch),
            nn.ReLU6()
        )
        self.pool1 = nn.AvgPool2d(kernel_size=7)
        self.Dense = nn.Linear(self.last_ch, 10)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bottleneck1(out)
        out = self.bottleneck2(out)
        out = self.bottleneck3(out)
        out = self.conv2(out)
        out = self.pool1(out)
        out = out.view(-1, self.last_ch)
        out = self.Dense(out)
        return out


def get_trainloader(batch_size):
    dataset = datasets.MNIST(root="./mmnist/", train=True, download=True,
                             transform=transforms.Compose([
                                 transforms.ToTensor(),
                                 transforms.Normalize(
                                     (mnist_mean,), (mnist_std,)
                                 )
                             ]))
    return data.DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
        drop_last=False,
    )


def get_testloader(batch_size):
    dataset = datasets.MNIST(root="./mmnist/", train=False, download=True,
                             transform=transforms.Compose([
                                 transforms.ToTensor(),
                                 transforms.Normalize(
                                     (mnist_mean,), (mnist_std,)
                                 )
                             ]))
    return data.DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        shuffle=False,                   # 每个epoch是否混淆
        num_workers=2,                   # 多进程并发装载
        pin_memory=True,                 # 是否使用锁页内存
        drop_last=False,                 # 是否丢弃最后一个不完整的batch
    )


def train(train_data_loader, optimizer):
    epoch_acc = 0
    epoch_loss = 0.0
    train_dataset_length = 0
    tot_it = len(train_data_loader)
    for it, (x_train, y_train) in enumerate(train_data_loader):
        if using_gpu:
            x_train, y_train = x_train.cuda(), y_train.cuda()
        train_dataset_length += len(y_train)
        y_pred = model(x_train)
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(y_pred, y_train)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
        epoch_acc += torch.argmax(y_pred, dim=1).eq(y_train).sum().item()

        if it % 32 == 0:
            print(f'it: [{it}/{tot_it}],'
                  f' Loss: {epoch_loss:.4f}/{it+1} = {epoch_loss/(it+1):.4f},'
                  f' Acc: {epoch_acc}/{train_dataset_length} = {100 * epoch_acc/train_dataset_length:.3f}%')

    print(f'\ntrain_Epoch:'
          f' Loss: {epoch_loss/tot_it:.4f},'
          f' Acc: {100 * epoch_acc/train_dataset_length:.3f}%')


def validation(test_data_loader):
    with torch.no_grad():
        model.eval()
        epoch_acc = 0
        epoch_loss = 0.0
        test_dataset_length = 0
        tot_it = len(test_data_loader)
        for it, (x_test, y_test) in enumerate(test_data_loader):
            test_dataset_length += len(y_test)
            if using_gpu:
                x_test, y_test = x_test.cuda(), y_test.cuda()
            y_pred = model(x_test)
            loss = nn.functional.cross_entropy(y_pred, y_test)
            epoch_loss += loss.item()
            epoch_acc += torch.argmax(y_pred, dim=1).eq(y_test).sum().item()

            if it % 32 == 0:
                print(f'it: [{it}/{tot_it}],'
                      f' Loss: {epoch_loss:.4f}/{it+1} = {epoch_loss / (it+1):.4f},'
                      f' Acc: {epoch_acc}/{test_dataset_length} = {100 * epoch_acc / test_dataset_length:.3f}%')
        model.train()
        print(f'\ntest_Epoch:'
              f' Loss: {epoch_loss/tot_it:.4f},'
              f' Acc: {100 * epoch_acc/test_dataset_length:.3f}%')


model = Model()
if using_gpu:
    model = model.cuda()


def main():
    PATH = './Mobilenetv2.pth'
    summary(model=model, input_size=(1, 28, 28))
    print(f'\n=== {["not using", "using"][using_gpu]} gpu ===')
    # pretrained_net = torch.load(PATH)
    # model.load_state_dict(pretrained_net)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    train_data_loader = get_trainloader(64)
    test_data_loader = get_testloader(64)
    for epoch in range(epoch_n):
        print(f'\n=== At epoch: [{epoch}/{epoch_n}] ===')
        train(train_data_loader=train_data_loader, optimizer=optimizer)
        validation(test_data_loader=test_data_loader)
    torch.save(model.state_dict(), PATH)


if __name__ == '__main__':
    main()