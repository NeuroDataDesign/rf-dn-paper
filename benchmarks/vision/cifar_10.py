"""
Coauthors: Haoyin Xu
           Yu-Chung Peng
"""
from toolbox import *

import argparse
import random
from sklearn.ensemble import RandomForestClassifier

import torchvision.models as models
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from sklearn.model_selection import ParameterSampler
import json
import os
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Subset


def tune_cnn(
    samples,
    classes_space,
    classifier,
    outputlist,
    cnn_kappa,
    cnn_ece,
    cnn_train_time,
    cnn_test_time,
):
    rng = np.random.RandomState(0)
    param_grid = {
        "lr": [0.0001, 0.001, 0.0125, 0.025],
        "mo": [0.01, 0.05, 0.1, 0.2],
        "bs": [32, 64, 128, 256],
        "wd": [0.00005, 0.0001, 0.0005, 0.001, 0.005],
    }
    param_list = list(ParameterSampler(param_grid, n_iter=20, random_state=rng))
    param_dict = [dict((k, v) for (k, v) in d.items()) for d in param_list]
    totalaccuracy = []
    for i in range(len(param_dict)):
        average_accuracy = 0
        for classes in classes_space:
            # train data
            cifar_trainset = datasets.CIFAR10(
                root="./", train=True, download=True, transform=data_transforms
            )
            # print(cifar_trainset.data.shape)
            cifar_train_labels = np.array(cifar_trainset.targets)
            # test data
            cifar_testset = datasets.CIFAR10(
                root="./", train=False, download=True, transform=data_transforms
            )
            """print(cifar_testset.data.shape)
            print(len(cifar_testset))
            print(cifar_testset[0])
            cifar_tuneset,cifar_testingset = torch.utils.data.random_split(cifar_testset,[5000,5000])
            print(len(cifar_tuneset))
            print(cifar_tuneset[0][1])
            tune_labels = np.array(cifar_tuneset.dataset.targets)
            print(len(tune_labels))
            #print(cifar_tuneset.data.shape)
            train_indices, test_indices, train_label, test_label = train_test_split(
                range(len(cifar_testset)),
                cifar_testset.targets,
                stratify=cifar_testset.targets,
                test_size=0.5,
                random_state=42
                )
            print(len(train_indices))
            train_split = Subset(cifar_testset, train_indices)
            train_label=np.array(train_label)
            print(train_label.shape)
            print(type(train_split))
            print(type(train_label))
            print(train_split[0])
            print(train_split[0][1])
            print(len(train_split))
            print(len(train_label))
            print("look here")
            #print(len(train_split[:]))
            test_split = Subset(cifar_testset.data, test_indices)
            print(test_split.dataset.data.shape)
            print(test_split)"""
            cifar_test_labels = np.array(cifar_testset.targets)
            if classifier == "cnn32":
                cnn = SimpleCNN32Filter(len(classes))
            elif classifier == "cnn32_2l":
                cnn = SimpleCNN32Filter2Layers(len(classes))
            elif classifier == "cnn32_5l":
                cnn = SimpleCNN32Filter5Layers(len(classes))
            elif classifier == "resnet18":
                cnn = models.resnet18(pretrained=True)
                num_ftrs = cnn.fc.in_features
                cnn.fc = nn.Linear(num_ftrs, len(classes))
            maxaccuracy = 0
            param = param_dict[i]
            (train_loader, valid_loader, test_loader,) = create_loaders_es(
                cifar_train_labels,
                cifar_test_labels,
                classes,
                cifar_trainset,
                cifar_testset,
                samples,
                param["bs"],
            )
            (cohen_kappa, ece, train_time, test_time, accuracy,) = test_dn_image_es(
                cnn,
                train_loader,
                valid_loader,
                test_loader,
                param["lr"],
                param["mo"],
                param["wd"],
            )
            print(accuracy)
            average_accuracy += accuracy
        average_accuracy = average_accuracy / len(classes_space)
        totalaccuracy.append(average_accuracy)
    totalaccuracynp = np.asarray(totalaccuracy)
    best_index = np.argmax(totalaccuracynp)
    num_classes = int(n_classes)
    sample_size = int(samples)
    outputdic = {}
    outputdic = param_dict[best_index].copy()
    outputdic["classifier"] = classifier
    outputlist.append(list(outputdic.values()))
    print("tuning is done")
    print(outputdic)
    return outputlist, cnn_kappa, cnn_ece, cnn_train_time, cnn_test_time, outputdic


def run_naive_rf():
    naive_rf_kappa = []
    naive_rf_ece = []
    naive_rf_train_time = []
    naive_rf_test_time = []
    for classes in classes_space:

        # cohen_kappa vs num training samples (naive_rf)
        for samples in samples_space:
            RF = RandomForestClassifier(n_estimators=100, n_jobs=-1)
            cohen_kappa, ece, train_time, test_time = run_rf_image_set(
                RF,
                cifar_train_images,
                cifar_train_labels,
                cifar_test_images,
                cifar_test_labels,
                samples,
                classes,
            )
            naive_rf_kappa.append(cohen_kappa)
            naive_rf_ece.append(ece)
            naive_rf_train_time.append(train_time)
            naive_rf_test_time.append(test_time)

    print("naive_rf finished")
    write_result(prefix + "naive_rf_kappa.txt", naive_rf_kappa)
    write_result(prefix + "naive_rf_ece.txt", naive_rf_ece)
    write_result(prefix + "naive_rf_train_time.txt", naive_rf_train_time)
    write_result(prefix + "naive_rf_test_time.txt", naive_rf_test_time)


def run_cnn(samples_space, classes_space, classifier):
    tune_cnn_kappa = []
    tune_cnn_ece = []
    tune_cnn_train_time = []
    tune_cnn_test_time = []
    cnn_kappa = []
    cnn_ece = []
    cnn_train_time = []
    cnn_test_time = []
    outputlist = []
    finaldic = {}
    for samples in samples_space:
        # train data
        """cifar_trainset = datasets.CIFAR10(
            root="./", train=True, download=True, transform=data_transforms
        )
        cifar_train_labels = np.array(cifar_trainset.targets)
        # test data
        cifar_testset = datasets.CIFAR10(
            root="./", train=False, download=True, transform=data_transforms
        )
        cifar_test_labels = np.array(cifar_testset.targets)
        # print(param["classifier"])"""
        (
            outputlist,
            tune_cnn_kappa,
            tune_cnn_ece,
            tune_cnn_train_time,
            tune_cnn_test_time,
            param,
        ) = tune_cnn(
            samples,
            classes_space,
            classifier,
            outputlist,
            tune_cnn_kappa,
            tune_cnn_ece,
            tune_cnn_train_time,
            tune_cnn_test_time,
        )
        # classifier = param["classifier"]
        finaldic[str(samples)] = list(param.values())
        finaldic["key"] = list(param.keys())
        for classes in classes_space:
            cifar_trainset = datasets.CIFAR10(
                root="./", train=True, download=True, transform=data_transforms
            )
            cifar_train_labels = np.array(cifar_trainset.targets)
            # test data
            cifar_testset = datasets.CIFAR10(
                root="./", train=False, download=True, transform=data_transforms
            )
            cifar_test_labels = np.array(cifar_testset.targets)
            if classifier == "cnn32":
                cnn = SimpleCNN32Filter(len(classes))
            elif classifier == "cnn32_2l":
                cnn = SimpleCNN32Filter2Layers(len(classes))
            elif classifier == "cnn32_5l":
                cnn = SimpleCNN32Filter5Layers(len(classes))
            elif classifier == "resnet18":
                cnn = models.resnet18(pretrained=True)
                num_ftrs = cnn.fc.in_features
                cnn.fc = nn.Linear(num_ftrs, len(classes))

            (
                train_loader,
                tuning_valid_loader,
                tuning_test_loader,
                test_valid_loader,
                test_test_loader,
            ) = create_loaders_es(
                cifar_train_labels,
                cifar_test_labels,
                classes,
                cifar_trainset,
                cifar_testset,
                samples,
                param["bs"],
            )
            cohen_kappa, ece, train_time, test_time, accuracy = test_dn_image_es(
                cnn,
                train_loader,
                test_valid_loader,
                test_test_loader,
                param["lr"],
                param["mo"],
                param["wd"],
            )
    print("runing is done")
    write_result(prefix + classifier + "_tune_kappa.txt", tune_cnn_kappa)
    write_result(prefix + classifier + "_tune_ece.txt", tune_cnn_ece)
    write_result(prefix + classifier + "_tune_train_time.txt", tune_cnn_train_time)
    write_result(prefix + classifier + "_tune_test_time.txt", tune_cnn_test_time)
    write_result(prefix + classifier + "_kappa.txt", cnn_kappa)
    write_result(prefix + classifier + "_ece.txt", cnn_ece)
    write_result(prefix + classifier + "_train_time.txt", cnn_train_time)
    write_result(prefix + classifier + "_test_time.txt", cnn_test_time)
    outputfile = prefix + classifier + "_parameters.json"
    with open(outputfile, "w") as outfile:
        json.dump(finaldic, outfile)


def run_cnn32_2l():
    cnn32_2l_kappa = []
    cnn32_2l_ece = []
    cnn32_2l_train_time = []
    cnn32_2l_test_time = []
    for classes in classes_space:

        # cohen_kappa vs num training samples (cnn32_2l)
        for samples in samples_space:
            # train data
            cifar_trainset = datasets.CIFAR10(
                root="./", train=True, download=True, transform=data_transforms
            )
            cifar_train_labels = np.array(cifar_trainset.targets)

            # test data
            cifar_testset = datasets.CIFAR10(
                root="./", train=False, download=True, transform=data_transforms
            )
            cifar_test_labels = np.array(cifar_testset.targets)

            cnn32_2l = SimpleCNN32Filter2Layers(len(classes))
            train_loader, valid_loader, test_loader = create_loaders_es(
                cifar_train_labels,
                cifar_test_labels,
                classes,
                cifar_trainset,
                cifar_testset,
                samples,
            )
            cohen_kappa, ece, train_time, test_time = run_dn_image_es(
                cnn32_2l,
                train_loader,
                valid_loader,
                test_loader,
            )
            cnn32_2l_kappa.append(cohen_kappa)
            cnn32_2l_ece.append(ece)
            cnn32_2l_train_time.append(train_time)
            cnn32_2l_test_time.append(test_time)

    print("cnn32_2l finished")
    write_result(prefix + "cnn32_2l_kappa.txt", cnn32_2l_kappa)
    write_result(prefix + "cnn32_2l_ece.txt", cnn32_2l_ece)
    write_result(prefix + "cnn32_2l_train_time.txt", cnn32_2l_train_time)
    write_result(prefix + "cnn32_2l_test_time.txt", cnn32_2l_test_time)


def run_cnn32_5l():
    cnn32_5l_kappa = []
    cnn32_5l_ece = []
    cnn32_5l_train_time = []
    cnn32_5l_test_time = []
    for classes in classes_space:

        # cohen_kappa vs num training samples (cnn32_5l)
        for samples in samples_space:
            # train data
            cifar_trainset = datasets.CIFAR10(
                root="./", train=True, download=True, transform=data_transforms
            )
            cifar_train_labels = np.array(cifar_trainset.targets)

            # test data
            cifar_testset = datasets.CIFAR10(
                root="./", train=False, download=True, transform=data_transforms
            )
            cifar_test_labels = np.array(cifar_testset.targets)

            cnn32_5l = SimpleCNN32Filter5Layers(len(classes))
            train_loader, valid_loader, test_loader = create_loaders_es(
                cifar_train_labels,
                cifar_test_labels,
                classes,
                cifar_trainset,
                cifar_testset,
                samples,
            )
            cohen_kappa, ece, train_time, test_time = run_dn_image_es(
                cnn32_5l,
                train_loader,
                valid_loader,
                test_loader,
            )
            cnn32_5l_kappa.append(cohen_kappa)
            cnn32_5l_ece.append(ece)
            cnn32_5l_train_time.append(train_time)
            cnn32_5l_test_time.append(test_time)

    print("cnn32_5l finished")
    write_result(prefix + "cnn32_5l_kappa.txt", cnn32_5l_kappa)
    write_result(prefix + "cnn32_5l_ece.txt", cnn32_5l_ece)
    write_result(prefix + "cnn32_5l_train_time.txt", cnn32_5l_train_time)
    write_result(prefix + "cnn32_5l_test_time.txt", cnn32_5l_test_time)


def run_resnet18():
    resnet18_kappa = []
    resnet18_ece = []
    resnet18_train_time = []
    resnet18_test_time = []
    for classes in classes_space:

        # cohen_kappa vs num training samples (resnet18)
        for samples in samples_space:
            # train data
            cifar_trainset = datasets.CIFAR10(
                root="./", train=True, download=True, transform=data_transforms
            )
            cifar_train_labels = np.array(cifar_trainset.targets)

            # test data
            cifar_testset = datasets.CIFAR10(
                root="./", train=False, download=True, transform=data_transforms
            )
            cifar_test_labels = np.array(cifar_testset.targets)

            res = models.resnet18(pretrained=True)
            num_ftrs = res.fc.in_features
            res.fc = nn.Linear(num_ftrs, len(classes))
            train_loader, valid_loader, test_loader = create_loaders_es(
                cifar_train_labels,
                cifar_test_labels,
                classes,
                cifar_trainset,
                cifar_testset,
                samples,
            )
            cohen_kappa, ece, train_time, test_time = run_dn_image_es(
                res,
                train_loader,
                valid_loader,
                test_loader,
            )
            resnet18_kappa.append(cohen_kappa)
            resnet18_ece.append(ece)
            resnet18_train_time.append(train_time)
            resnet18_test_time.append(test_time)

    print("resnet18 finished")
    write_result(prefix + "resnet18_kappa.txt", resnet18_kappa)
    write_result(prefix + "resnet18_ece.txt", resnet18_ece)
    write_result(prefix + "resnet18_train_time.txt", resnet18_train_time)
    write_result(prefix + "resnet18_test_time.txt", resnet18_test_time)


if __name__ == "__main__":
    torch.multiprocessing.freeze_support()

    # Example usage: python cifar_10.py -m 3
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", help="class number")
    args = parser.parse_args()
    n_classes = int(args.m)
    prefix = args.m + "_class/"
    samples_space = np.geomspace(10, 10000, num=8, dtype=int)

    nums = list(range(10))
    random.shuffle(nums)
    classes_space = list(combinations_45(nums, n_classes))

    # normalize
    scale = np.mean(np.arange(0, 256))
    normalize = lambda x: (x - scale) / scale

    # train data
    cifar_trainset = datasets.CIFAR10(
        root="./", train=True, download=True, transform=None
    )
    cifar_train_images = normalize(cifar_trainset.data)
    cifar_train_labels = np.array(cifar_trainset.targets)

    # test data
    cifar_testset = datasets.CIFAR10(
        root="./", train=False, download=True, transform=None
    )
    cifar_test_images = normalize(cifar_testset.data)
    cifar_test_labels = np.array(cifar_testset.targets)

    cifar_train_images = cifar_train_images.reshape(-1, 32 * 32 * 3)
    cifar_test_images = cifar_test_images.reshape(-1, 32 * 32 * 3)

    # run_naive_rf()

    data_transforms = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )
    run_cnn(samples_space, classes_space, "cnn32")
    run_cnn(samples_space, classes_space, "cnn32_2l")
    run_cnn(samples_space, classes_space, "cnn32_5l")
    # run_cnn32()
    # run_cnn32_2l()
    # run_cnn32_5l()

    data_transforms = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    run_cnn(samples_space, classes_space, "resnet18")
    # run_resnet18()
