# coding: utf-8


# Catch passed auguments from run script.
import importlib, sys, os, json
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--mode", type=str, default="train",
                    help="Run mode, train or analyze.")
parser.add_argument("--data_dir", type=str, default="data",
                    help="Data folder name.")
parser.add_argument("--data_name", type=str, default="fact-checks",
                    help="Dataset name.")
parser.add_argument("--config_name", type=str, default="soft_rationalizer_w_domain",
                    help="Dataset name.")
parser.add_argument("--random_seed", type=str, default=0,
                    help="Random seed")
args, _ = parser.parse_known_args()
args.data_path = os.path.join(args.data_dir, args.data_name)

# Read train arguments from .config file.
args.config_dir = os.path.join(args.data_path, args.config_name + ".config")
with open(args.config_dir, "r") as f:
    config = json.load(f)
train_args = argparse.Namespace(**config)
if train_args.embedding_name == "glove":
    train_args.embedding_dir = os.path.join(
        args.data_dir,
        train_args.embedding_name,
        train_args.embedding_name + ".6B.%sd.txt" % train_args.embedding_dim
    )
elif train_args.embedding_name == "trained":
    train_args.embedding_dir = os.path.join(args.data_path, "w2v.txt")
train_args.working_dir = os.path.join(args.data_path, args.config_name + ".ckpt")

# Set GPU chips.
import torch
if torch.cuda.device_count() > 1:
    torch.cuda.set_device(int(train_args.gpu_id))
    
# Set random seeds.
import numpy as np
import random
torch.manual_seed(args.random_seed)
np.random.seed(args.random_seed)
random.seed(args.random_seed)


# Train or analyze a model.
if args.mode in {"train", "output"}:

    # Load data.
    from datasets.dataset_loader import ClassificationData
    data = ClassificationData(args.data_path, train_args)  # Load data.
    train_args.num_labels = len(data.label_vocab)  # Number of labels.
    print("Data successfully loaded:", data)

    if args.mode == "train":  # Train a model.

        # Initialize checkpoints.
        from utils.checkpointer import init_ckpt
        init_ckpt(train_args.working_dir)

        # Initialize embeddings.
        embeddings = data.initial_embedding(train_args.embedding_method,
                                            train_args.embedding_dim,
                                            train_args.embedding_dir)  # Load embeddings.
        print("Embeddings successfully initialized:", embeddings.shape)
        
        # Initialize model.
        from utils.formatter import format_class
        Model = getattr(importlib.import_module("models." + train_args.model_name),
                        format_class(train_args.model_name))
        model = Model(embeddings, train_args)
        print("Model successfully initialized:", model)
        num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print("# of parameters:", num_params)

        # Train model.
        from runners.trainer import train
        train(model, data, train_args)
        print("Model successfully trained.")
    
    elif args.mode == "output":  # Output rationales.
        
        # Get best checkpoint.
        from utils.checkpointer import find_best_ckpt
        ckpt_path = find_best_ckpt(train_args.working_dir)
        print("Best checkpoint found:", ckpt_path)

        # Output rationales.
        out_path = os.path.join(args.data_path, args.config_name + ".output")
        outputer = importlib.import_module("analyzers.output_rationales")
        outputer.output(ckpt_path, out_path, data, train_args)
        print("Rationales successfully output.")


elif args.mode in {"eval", "evaluate"}:

    # Get best checkpoint.
    from utils.checkpointer import find_best_ckpt
    ckpt_path = find_best_ckpt(train_args.working_dir)
    print("Best checkpoint found:", ckpt_path)


elif args.mode == "binarize":
    
    # Output rationales.
    out_path = os.path.join(args.data_path, args.config_name + ".output")
    outputer = importlib.import_module("analyzers.binarize_rationales")
    outputer.binarize(out_path, train_args)
    print("Rationales successfully binarized.")


elif args.mode in {"vector", "vectorize"}:

    # Vectorize rationales.
    out_path = os.path.join(args.data_path, args.config_name + ".output")
    vector_path = os.path.join(args.data_path, args.config_name + ".vector")
    vectorizer = importlib.import_module("analyzers.vectorize_rationales")
    vectorizer.vectorize(args.data_path, out_path, vector_path, train_args)
    print("Rationales successfully vectorized.")


elif args.mode == "cluster":

    # Cluster rationales.
    vector_path = os.path.join(args.data_path, args.config_name + ".vector")
    cluster_path = os.path.join(args.data_path, args.config_name + ".cluster")
    cluster = importlib.import_module("analyzers.cluster_rationales")
    cluster.clust(vector_path, cluster_path, train_args)
    print("Rationales successfully clustered.")


elif args.mode == "test":
    
    # Test data.
    from datasets.dataset_loader import test_data
    test_data(args.data_path, train_args)
    print("Model successfully tested:", args.data_name)
    
    # Test model.
    test_model = getattr(importlib.import_module("models." + train_args.model_name),
                         "test_" + train_args.model_name)
    test_model(train_args)
    print("Model successfully tested:", train_args.model_name)


elif args.mode == "purge":

    # Purge all checkpoints and analyses.
    from utils.checkpointer import purge
    purge(os.path.join(args.data_path, args.config_name + ".ckpt"))
    purge(os.path.join(args.data_path, args.config_name + ".analyze"))
    print("All checkpoints and analyses purged.")


else:
    exit("Wrong mode.")
