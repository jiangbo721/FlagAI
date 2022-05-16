from flagai.trainer import Trainer
from flagai.model.glm_model import GLMForSingleTokenCloze, GLMForMultiTokenCloze, GLMForMultiTokenClozeFast
from flagai.data.tokenizer import GLMLargeEnWordPieceTokenizer, GLMLargeChTokenizer

from flagai.data.dataset import SuperGlueDataset
from flagai.test_utils import CollateArguments
from flagai.data.dataset.superglue.control import DEFAULT_METRICS, MULTI_TOKEN_TASKS, CH_TASKS
import unittest
from flagai.data.dataset import ConstructSuperglueStrategy


class TrainerTestCase(unittest.TestCase):

    def test_init_trainer_pytorch(self):
        # task_name options: ['boolq', 'cb', 'copa', 'multirc', 'rte', 'wic', 'wsc', 'afqmc', 'tnews']
        task_name = "wsc"

        trainer = Trainer(env_type='pytorch',
                          epochs=10,
                          batch_size=4,
                          eval_interval=100,
                          log_interval=50,
                          experiment_name='glm_large',
                          pytorch_device='cuda',
                          load_dir=None,
                          lr=1e-4)
        print("downloading...")

        cl_args = CollateArguments()
        cl_args.multi_token = task_name in MULTI_TOKEN_TASKS

        if task_name in CH_TASKS:
            model_name = 'glm_large_ch'
            tokenizer = GLMLargeChTokenizer(add_block_symbols=True,
                                            add_task_mask=False,
                                            add_decoder_mask=False,
                                            fix_command_token=True)
        else:
            model_name = 'glm_large_en'
            tokenizer = GLMLargeEnWordPieceTokenizer()

        if cl_args.multi_token:
            model = GLMForMultiTokenCloze.from_pretrain(model_name=model_name)
        else:
            model = GLMForSingleTokenCloze.from_pretrain(model_name=model_name)

        train_dataset = SuperGlueDataset(task_name=task_name,
                                         data_dir='./datasets/',
                                         dataset_type='train',
                                         tokenizer=tokenizer)

        collate_fn = ConstructSuperglueStrategy(cl_args,
                                                tokenizer,
                                                task_name=task_name)

        valid_dataset = SuperGlueDataset(task_name=task_name,
                                         data_dir='./datasets/',
                                         dataset_type='dev',
                                         tokenizer=tokenizer)

        metric_methods = DEFAULT_METRICS[task_name]
        trainer.train(model,
                      collate_fn=collate_fn,
                      train_dataset=train_dataset,
                      valid_dataset=valid_dataset,
                      metric_methods=metric_methods)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TrainerTestCase('test_init_trainer_pytorch'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())