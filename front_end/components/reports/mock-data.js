export const mockData = {
  summary: {
    totalHypotheses: 12,
    completed: 8,
    running: 2,
    failed: 2,
    avgEffectSize: 0.73,
    supported: 5,
    refuted: 3,
    inconclusive: 4
  },
  hypotheses: [
    {
      id: "H001",
      paper: "Attention Is All You Need",
      claim: "Transformer models outperform RNN-based models on translation tasks",
      status: "completed",
      metrics: {
        effectSize: 0.85,
        pValue: 0.001,
        confidenceInterval: [0.76, 0.94],
        accuracy: 0.92,
        f1Score: 0.89
      },
      verdict: "supported",
      preregisteredPlan: {
        method: "Comparative analysis of BLEU scores",
        dataset: "WMT14 English-German",
        parameters: {
          learningRate: 0.0001,
          batchSize: 64,
          epochs: 10
        }
      },
      code: "import torch\nimport transformers\n\ndef run_experiment():\n    # Load models\n    transformer = transformers.AutoModel.from_pretrained('bert-base-uncased')\n    rnn_model = LegacyRNNModel()\n    \n    # Load dataset\n    dataset = load_wmt14()\n    \n    # Run comparison\n    transformer_results = evaluate(transformer, dataset)\n    rnn_results = evaluate(rnn_model, dataset)\n    \n    # Calculate statistics\n    effect_size = cohen_d(transformer_results, rnn_results)\n    p_value = t_test(transformer_results, rnn_results)\n    \n    return {\n        'effect_size': effect_size,\n        'p_value': p_value,\n        'transformer_bleu': transformer_results['bleu'],\n        'rnn_bleu': rnn_results['bleu']\n    }\n",
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:8f4c2d56",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" },
            { name: "transformers", version: "4.5.1" }
          ]
        }
      },
      artifacts: {
        report: "report_H001.pdf",
        bundle: "artifacts_H001.zip",
        versions: [
          { id: "v1", date: "2023-05-10" },
          { id: "v2", date: "2023-05-15" }
        ]
      },
      plots: [
        { 
          title: "BLEU Score Comparison", 
          type: "bar",
          data: {
            labels: ["Transformer", "RNN"],
            values: [32.5, 26.1]
          }
        },
        {
          title: "Training Loss",
          type: "line",
          data: {
            labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            values: [
              [2.3, 1.8, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.5, 0.5],
              [2.4, 2.0, 1.8, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0]
            ]
          }
        }
      ]
    },
    {
      id: "H002",
      paper: "BERT: Pre-training of Deep Bidirectional Transformers",
      claim: "BERT outperforms previous methods on GLUE benchmark",
      status: "completed",
      metrics: {
        effectSize: 0.92,
        pValue: 0.0005,
        confidenceInterval: [0.85, 0.99],
        accuracy: 0.94,
        f1Score: 0.93
      },
      verdict: "supported",
      preregisteredPlan: {
        method: "Evaluation on GLUE benchmark",
        dataset: "GLUE",
        parameters: {
          learningRate: 5e-5,
          batchSize: 32,
          epochs: 3
        }
      },
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:7a3d9f12",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" },
            { name: "transformers", version: "4.5.1" }
          ]
        }
      },
      artifacts: {
        report: "report_H002.pdf",
        bundle: "artifacts_H002.zip",
        versions: [
          { id: "v1", date: "2023-06-01" }
        ]
      }
    },
    {
      id: "H003",
      paper: "Deep Residual Learning for Image Recognition",
      claim: "ResNet-50 achieves better accuracy than VGG-16 with fewer parameters",
      status: "completed",
      metrics: {
        effectSize: 0.68,
        pValue: 0.01,
        confidenceInterval: [0.58, 0.78],
        accuracy: 0.76,
        f1Score: 0.74
      },
      verdict: "supported",
      preregisteredPlan: {
        method: "Comparative analysis on ImageNet",
        dataset: "ImageNet",
        parameters: {
          learningRate: 0.1,
          batchSize: 256,
          epochs: 90
        }
      },
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:3e7c8f45",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" },
            { name: "torchvision", version: "0.10.0" }
          ]
        }
      },
      artifacts: {
        report: "report_H003.pdf",
        bundle: "artifacts_H003.zip",
        versions: [
          { id: "v1", date: "2023-04-15" }
        ]
      }
    },
    {
      id: "H004",
      paper: "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
      claim: "Dropout significantly reduces overfitting in deep neural networks",
      status: "completed",
      metrics: {
        effectSize: 0.45,
        pValue: 0.08,
        confidenceInterval: [0.38, 0.52],
        accuracy: 0.83,
        f1Score: 0.81
      },
      verdict: "refuted",
      preregisteredPlan: {
        method: "Comparative analysis with/without dropout",
        dataset: "MNIST",
        parameters: {
          learningRate: 0.01,
          batchSize: 128,
          epochs: 20,
          dropoutRate: 0.5
        }
      },
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:9f7c6d23",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" }
          ]
        }
      },
      artifacts: {
        report: "report_H004.pdf",
        bundle: "artifacts_H004.zip",
        versions: [
          { id: "v1", date: "2023-03-20" }
        ]
      }
    },
    {
      id: "H005",
      paper: "Adam: A Method for Stochastic Optimization",
      claim: "Adam optimizer converges faster than SGD with momentum",
      status: "running",
      metrics: {
        effectSize: null,
        pValue: null,
        confidenceInterval: null,
        accuracy: null,
        f1Score: null
      },
      verdict: null,
      preregisteredPlan: {
        method: "Comparative analysis of convergence rates",
        dataset: "CIFAR-10",
        parameters: {
          learningRateAdam: 0.001,
          learningRateSGD: 0.01,
          batchSize: 128,
          epochs: 50
        }
      },
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:5e8f2a17",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" },
            { name: "torchvision", version: "0.10.0" }
          ]
        }
      },
      artifacts: {
        report: null,
        bundle: null,
        versions: []
      }
    },
    {
      id: "H006",
      paper: "Batch Normalization: Accelerating Deep Network Training",
      claim: "Batch normalization allows higher learning rates and faster convergence",
      status: "failed",
      metrics: null,
      verdict: null,
      preregisteredPlan: {
        method: "Comparative analysis with/without batch normalization",
        dataset: "CIFAR-100",
        parameters: {
          learningRate: [0.1, 0.01, 0.001],
          batchSize: 128,
          epochs: 100
        }
      },
      reproducibilityInfo: {
        randomSeed: 42,
        datasetHash: "sha256:2c7d9f34",
        environment: {
          pythonVersion: "3.8.10",
          packages: [
            { name: "torch", version: "1.9.0" },
            { name: "torchvision", version: "0.10.0" }
          ]
        }
      },
      artifacts: {
        report: null,
        bundle: null,
        versions: []
      }
    }
  ]
};