 #!/usr/bin/python3.5
# -*- coding: utf-8 -*-
"""
Voxnet implementation on tensorflow
"""
import tensorflow as tf
import numpy as np
import os
from glob import glob
import random


# TODO: (vincent.cheung.mcer@gmail.com) combine generator `gen_batch_function` and data collector `get_all_data` into a class
def gen_batch_function(data_folder,batch_size):
    """
    Generate function to create batches of training data.
    
    Args:
    `data_folder`:path to folder that contains all the `npy` datasets.
    
    Ret:
    `get_batches_fn`:generator function(batch_size)
    """
    def get_batches_fn(batch_size):
        """
        Create batches of training data.

        Args:
        `batch_size`:Batch Size

        Ret:
        return Batches of training data
        """
        grid_paths = glob(os.path.join(data_folder, 'voxel_npy', '*.npy'))
        # TODO:(vincent.cheung.mcer@gmail.com) not yet add support for multiresolution npy data
        # grid_paths_r2 = glob(os.path.join(data_folder, 'voxel_npy_r2', '*.npy'))
        
        # shuffle data
        random.shuffle(grid_paths)

        for batch_i in range(0, len(grid_paths), batch_size):
            grids = []
            labels = []
            for grid_path in grid_paths[batch_i:batch_i+batch_size]:
                # extract the label from path+file_name: e.g.`./voxel_npy/pillar.2.3582_12.npy`
                file_name = grid_path.split('/')[-1] #`pillar.2.3582_12.npy`
                label = SUOD_label_dictionary[file_name.split('.')[0]] #dict[`pillar`]
                # load *.npy
                grid = np.load(grid_path)
                labels.append(label)
                grids.append(grid)
                
            yield np.array(grids), np.array(labels)
    return get_batches_fn(batch_size)


def save_inference_sample(argv):
    """
    Print the predicted class and ground truth class.

    Args:
    `argv`:['./',model_dir,data_folder] a tuple of args.
    `model_dir`:the folder of trained model
    `data_folder`:the folder of `*.npy` data to be inferred
    """
    # Use default setting
    if len(argv) != 3:
        print ('len(argv) is {}, use default setting'.format(len(argv)))
        model_dir = './voxnet_r2_bk/'
        data_folder = './'
    else:
        model_dir = argv[1]
        data_folder = argv[2]

    voxet = Voxnet()
    # Voxnet Estimator: model init
    voxel_classifier = tf.estimator.Estimator(
        model_fn=voxet.voxnet_fn, model_dir=model_dir)

    # Evaluating data collector
    eval_grids_list, eval_labels_list = get_all_data(data_folder,mode='eval')
    eval_data = np.array(eval_grids_list)
    eval_labels = np.array(eval_labels_list)

    # Evaluate the model and print results
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": eval_data},
    num_epochs=1,
    shuffle=False)
    # Get predictions
    predictions = voxel_classifier.predict(input_fn=eval_input_fn)

    # list for F1 score calculations
    lab=[]# label
    prd=[]# predictions
    # Print results
    for dict_predict, gt in zip(predictions,eval_labels):
        lab.append(gt)# adding label list
        prd.append(dict_predict['classes'])# adding prediction list
        print ('predicted class:{}-{}, ground truth:{}-{}'.format(dict_predict['classes'],
        SUOD_label_dictionary_rev[str(dict_predict['classes'])],
        gt,
        SUOD_label_dictionary_rev[str(gt)]
        ))

    # F1 score calculations
    import sklearn.metrics
    print ('The F1 score of current model:{} is {}'.format(model_dir,sklearn.metrics.f1_score(lab,prd,average='weighted')))

    # TODO: (vincent.cheung.mcer@gmail.com) to count TP\FP\TN\FN of different classes and adding top-3 class score

def get_infer_data(data_folder, sub_path = 'test_data_npy_eval_r2', type='dense'):
    """
    Get all voxels and corresponding labels from `data_folder`.

    Args:
    `data_folder`:path to the folder that contains `voxel_npy_train` and `voxel_npy_eval`.
    `sub_path`:folder that contains all the `npy` datasets 
    `type`:type of npy for future use in sparse tensor, values={`dense`,`sparse`} 

    Ret:
    `grids`:list of voxel grids
    `labels`:list of labels
    """
    sub_path = sub_path
    grid_paths = glob(os.path.join(data_folder, sub_path, '*.npy'))
    
    # TODO:(vincent.cheung.mcer@gmail.com) not yet add support for multiresolution npy data
    # TODO:(vincent.cheung.mcer@gmail.com) not yet support sparse npy
    # grid_paths_r2 = glob(os.path.join(data_folder, 'voxel_npy_r2', '*.npy'))    
    grids=[]
    labels=[]
    for grid_path in grid_paths:
        # extract the label from path+file_name: e.g.`./voxel_npy/pillar.2.3582_12.npy`
        file_name = grid_path.split('/')[-1] #`pillar.2.3582_12.npy`
        label = file_name.split('.')[0]#dict[`pillar`]
        # load *.npy
        grid = np.load(grid_path).astype(np.float32)
        labels.append(label)
        grids.append(grid)
    return grids, labels

def inference(argv):
    """
    Print the predicted class and ground truth class.

    Args:
    `argv`:['./',model_dir,data_folder] a tuple of args.
    `model_dir`:the folder of trained model
    `data_folder`:the folder of `*.npy` data to be inferred
    """
    # Use default setting
    if len(argv) != 4:
        print ('len(argv) is {}, use default setting'.format(len(argv)))
        model_dir = './voxnet_r2_bk/'
        data_folder = './'
        sub_path = 'test_data_npy_eval_r2'
    else:
        model_dir = argv[1]
        data_folder = argv[2]
        sub_path = argv[3]

    voxet = Voxnet()
    # Voxnet Estimator: model init
    voxel_classifier = tf.estimator.Estimator(
        model_fn=voxet.voxnet_fn, model_dir=model_dir)

    # Evaluating data collector
    eval_grids_list, eval_labels_list = get_infer_data(data_folder,sub_path)
    eval_data = np.array(eval_grids_list)
    eval_labels = np.array(eval_labels_list)

    # Evaluate the model and print results
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
    x={"x": eval_data},
    num_epochs=1,
    shuffle=False)
    # Get predictions
    predictions = voxel_classifier.predict(input_fn=eval_input_fn)

    # Print results
    top_k = 3
    for dict_predict,gt in zip(predictions,eval_labels):
        print ('predicted class:{}-{}, file name:{}'.format(
            dict_predict['classes'],
            SUOD_label_dictionary_rev[str(dict_predict['classes'])],
            gt))
        # Top K label, k =3
        """
        Code sample of top k index
        In [1]: import numpy as np
        In [2]: arr = np.array([1, 3, 2, 4, 5])
        In [3]: arr.argsort()[-3:][::-1]
        Out[3]: array([4, 3, 1])...
        """
        arr = dict_predict['probabilities']
        idx = arr.argsort()[-top_k:][::-1]
        print ('Top K label:{} {} {}'.format(SUOD_label_dictionary_rev[str(idx[0])],
            SUOD_label_dictionary_rev[str(idx[1])],
            SUOD_label_dictionary_rev[str(idx[2])]))


class Voxnet(object):
    def __init__(self, learning_rate=0.001, num_classes=14, batch_size=32, epochs=64):
        """
        Init paramters
        """
        self.num_classes = num_classes
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        # to enable tf logging info
        tf.logging.set_verbosity(tf.logging.INFO)

    def voxnet_fn(self, features, labels, mode):
        """
        Voxnet tensorflow graph.
        It follows description from this TensorFlow tutorial:
        `https://www.tensorflow.org/versions/master/tutorials/mnist/pros/index.html#deep-mnist-for-experts`
        
        Args:
        `features`: default paramter for tf.model_fn
        `labels`: default paramter for tf.model_fn
        `mode`: default paramter for tf.model_fn

        Ret:
        `EstimatorSpec`:    predictions/loss/train_op/eval_metric_ops in EstimatorSpec object
        """
        input_layer = tf.reshape(features['x'], [-1, 32, 32, 32, 1])

        # Layer 1: 3D conv(filters_num=32, filter_kernel_size=5, strides=2)
        # Input(32*32*32), Output:(14*14*14)*32
        conv1 = tf.layers.conv3d(inputs=input_layer, filters=32, kernel_size=[5,5,5], strides=[2,2,2],name='conv1')

        # Layer 2: 3D conv(filters_num=32, filter_kernel_size=3, strides=1)
        # Max-pooling (2*2*2)
        # Input(32*32*32)*32, Output:(6*6*6)*32
        conv2 = tf.layers.conv3d(inputs=conv1, filters=32, kernel_size=[3,3,3], strides=[1,1,1],name='conv2')
        # TODO: (vincent.cheung.mcer@gmail.com) not sure about the pool_size
        max_pool1 = tf.layers.max_pooling3d(inputs=conv2, pool_size=2,strides=2)
        # TODO: (vincent.cheung.mcer@gmail.com), later can try 3D conv instead of Fully Connect dense layer
        max_pool1_flat = tf.reshape(max_pool1, [-1,6*6*6*32])

        # Layer 3: Fully Connected 128
        # Input (6*6*6)*32, Output:(128)
        dense4 = tf.layers.dense(inputs=max_pool1_flat, units=128)

        # Layer 4: Fully Connected Output
        # Input: (128), Output:K class
        dense5 = tf.layers.dense(inputs=dense4, units=self.num_classes)
        logits = dense5

        predictions = {
            # Generate predictions (for PREDICT and EVAL mode)
            'classes': tf.argmax(input=logits, axis=1),
            # Add `softmax_tensor` to the graph. It is used for PREDICT and by the `logging_hook`.
            'probabilities': tf.nn.softmax(logits, name='softmax_tensor')
        }

        if mode == tf.estimator.ModeKeys.PREDICT:
            return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

        # Calculate Loss (for both TRAIN and EVAL modes)
        onehot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32), depth=self.num_classes)
        loss = tf.losses.softmax_cross_entropy(onehot_labels=onehot_labels, logits=logits)
        tf.summary.scalar("loss", loss)
        # Configure the Training Op (for TRAIN mode)
        if mode == tf.estimator.ModeKeys.TRAIN:
            optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
            train_op = optimizer.minimize(
                loss=loss,
                global_step=tf.train.get_global_step())
            return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)

        # Add evaluation metrics (for EVAL mode)
        eval_metric_ops = {'accuracy': tf.metrics.accuracy(labels=labels, predictions=predictions['classes'])}

        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)


def main(argv,data_folder='./',batch_size=32,epochs=8):
    """
    The main function for voxnet training and evaluation.
    """
    voxet = Voxnet()
    # Voxnet Estimator: model init
    voxel_classifier = tf.estimator.Estimator(model_fn=voxet.voxnet_fn, model_dir='./voxnet/')

    # Trainning data collector
    grids_list, labels_list = get_all_data(data_folder, mode='train')
    train_data = np.array(grids_list)
    train_labels = np.array(labels_list)

    # Evaluating data collector
    eval_grids_list, eval_labels_list = get_all_data(data_folder, mode='eval')
    eval_data = np.array(eval_grids_list)
    eval_labels = np.array(eval_labels_list)

    print('data get')

    # Set up logging for predictions
    tensors_to_log = {"probabilities": "softmax_tensor"}
    logging_hook = tf.train.LoggingTensorHook(
        tensors=tensors_to_log, every_n_iter=10)

    # Train the model
    train_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": train_data},
        y=train_labels,
        batch_size=batch_size,
        num_epochs=epochs,
        shuffle=True)

    print ('train start')

    voxel_classifier.train(
        input_fn=train_input_fn,
        steps=5000,
        hooks=[logging_hook])
    
    print('train done')

    # Evaluate the model and print results
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": eval_data},
        y=eval_labels,
        num_epochs=1,
        shuffle=False)
    eval_results = voxel_classifier.evaluate(input_fn=eval_input_fn)
    print(eval_results)

if __name__ == '__main__':
    # run the main function and model_fn, according to Tensorflow R1.3 API
    #tf.app.run(main=main, argv=['./'])
    #tf.app.run(main=save_inference_sample, argv=['./','./voxnet_r2_bk/','./'])
    tf.app.run(main=inference, argv=['./','./voxnet_r2_bk/','./'])