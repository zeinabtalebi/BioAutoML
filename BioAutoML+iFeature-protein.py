import warnings
warnings.filterwarnings(action='ignore', category=FutureWarning)
warnings.filterwarnings('ignore')
import pandas as pd
import argparse
import subprocess
# import shutil
import sys
import os.path
import time
import shutil
import xgboost as xgb
import lightgbm as lgb
import json
from catboost import CatBoostClassifier
from sklearn.metrics import balanced_accuracy_score
# from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from sklearn.metrics import f1_score
from hyperopt import hp, fmin, tpe, STATUS_OK, Trials
from functools import reduce

# Testing
# python BioAutoML-feature.py
# -fasta_train Case\ Studies/CS-II/train/miRNA.fasta
# Case\ Studies/CS-II/train/pre_miRNA.fasta
# Case\ Studies/CS-II/train/tRNA.fasta
# -fasta_label_train miRNA pre_miRNA tRNA
# -fasta_test Case\ Studies/CS-II/test/miRNA.fasta
# Case\ Studies/CS-II/test/pre_miRNA.fasta
# Case\ Studies/CS-II/test/tRNA.fasta
# -fasta_label_test miRNA pre_miRNA tRNA
# -output results/


def objective_rf(space):

	"""Automated Feature Engineering - Objective Function - Bayesian Optimization"""

	position = int((len(df_x.columns) - 5046) / 2)
	index = list()
	descriptors = {'Shannon': list(range(0, 5)), 'Tsallis_23': list(range(5, 10)),
				   'Tsallis_30': list(range(10, 15)), 'Tsallis_40': list(range(15, 20)),
				   'ComplexNetworks': list(range(20, 98)), 'kGap_di': list(range(98, 498)),
				   'AAC': list(range(498, 518)),
				   'DPC': list(range(518, 918)),
				   'CKSAAP': list(range(918, 3318)), 
			 	   'DDE': list(range(3318, 3718)),
			 	   'GAAC': list(range(3718, 3723)),
			 	   'CKSAAGP': list(range(3723, 3873)),
			 	   'GDPC': list(range(3873, 3898)),
			 	   'GTPC': list(range(3898, 4023)),
			 	   'CTDC': list(range(4023, 4062)),
			 	   'CTDT': list(range(4062, 4101)),
			 	   'CTDD': list(range(4101, 4296)),
			 	   'CTriad': list(range(4296, 4639)),
			 	   'KSCTriad': list(range(4639, 4982)), 
				   'Global': list(range(4982, 4992)),
				   'Peptide': list(range(4992, 5008)),
				   'Fourier_Integer': list(range(5008, 5027)),
				   'Fourier_EIIP': list(range(5027, 5046)),
				   'EIIP': list(range(5046, (5046 + position))),
				   'AAAF': list(range((5046 + position), len(df_x.columns)))} 

	for descriptor, ind in descriptors.items():
		if int(space[descriptor]) == 1:
			index = index + ind

	x = df_x.iloc[:, index]

	# print(index)
	# print(space)

	if int(space['Classifier']) == 0:
		if len(fasta_label_train) > 2:
			model = AdaBoostClassifier(random_state=63)
		else:
			model = CatBoostClassifier(n_estimators=200,
									   thread_count=n_cpu, nan_mode='Max',
								   	   logging_level='Silent', random_state=63)
	elif int(space['Classifier']) == 1:
		model = RandomForestClassifier(n_estimators=500, n_jobs=n_cpu, random_state=63)
	elif int(space['Classifier']) == 2:
		model = lgb.LGBMClassifier(n_estimators=500, n_jobs=n_cpu, random_state=63)
	else:
		model = xgb.XGBClassifier(eval_metric='mlogloss', random_state=63)

	# print(model)

	if len(fasta_label_train) > 2:
		score = make_scorer(f1_score, average='weighted')
	else:
		score = make_scorer(balanced_accuracy_score)

	kfold = StratifiedKFold(n_splits=10, shuffle=True)
	metric = cross_val_score(model,
							 x,
							 labels_y,
							 cv=kfold,
							 scoring=score,
							 n_jobs=n_cpu).mean()

	# print(metric)

	return {'loss': -metric, 'status': STATUS_OK}


def feature_engineering(estimations, train, train_labels, test, foutput):

	"""Automated Feature Engineering - Bayesian Optimization"""

	global df_x, labels_y

	print('Automated Feature Engineering - Bayesian Optimization')

	df_x = pd.read_csv(train)
	labels_y = pd.read_csv(train_labels)
	# print(df_x.shape)

	if test != '':
		df_test = pd.read_csv(test)

	path_bio = foutput + '/best_descriptors'
	if not os.path.exists(path_bio):
		os.mkdir(path_bio)

	param = {'Shannon': [0, 1], 'Tsallis_23': [0, 1],
			 'Tsallis_30': [0, 1], 'Tsallis_40': [0, 1],
			 'ComplexNetworks': [0, 1],
			 'kGap_di': [0, 1],
			 'AAC': [0, 1], 'DPC': [0, 1],
			 'CKSAAP': [0, 1],
			 'DDE': [0, 1],
			 'GAAC': [0, 1],
			 'CKSAAGP': [0, 1],
			 'GDPC': [0, 1],
			 'GTPC': [0, 1],
			 'CTDC': [0, 1],
			 'CTDT': [0, 1],
			 'CTDD': [0, 1],
			 'CTriad': [0, 1],
			 'KSCTriad': [0, 1],
			 'Global': [0, 1],
			 'Peptide': [0, 1],
			 'Fourier_Integer': [0, 1],
			 'Fourier_EIIP': [0, 1], 'EIIP': [0, 1],
			 'AAAF': [0, 1],
			 'Classifier': [0, 1, 2, 3]}

	space = {'Shannon': hp.choice('Shannon', [0, 1]),
			 'Tsallis_23': hp.choice('Tsallis_23', [0, 1]),
			 'Tsallis_30': hp.choice('Tsallis_30', [0, 1]),
			 'Tsallis_40': hp.choice('Tsallis_40', [0, 1]),
			 'ComplexNetworks': hp.choice('ComplexNetworks', [0, 1]),
			 'kGap_di': hp.choice('kGap_di', [0, 1]),
			 'AAC': hp.choice('AAC', [0, 1]),
			 'DPC': hp.choice('DPC', [0, 1]),
			 'CKSAAP': hp.choice('CKSAAP', [0, 1]),
			 'DDE': hp.choice('DDE', [0, 1]),
			 'GAAC': hp.choice('GAAC', [0, 1]),
			 'CKSAAGP': hp.choice('CKSAAGP', [0, 1]),
			 'GDPC': hp.choice('GDPC', [0, 1]),
			 'GTPC': hp.choice('GTPC', [0, 1]),
			 'CTDC': hp.choice('CTDC', [0, 1]),
			 'CTDT': hp.choice('CTDT', [0, 1]),
			 'CTDD': hp.choice('CTDD', [0, 1]),
			 'CTriad': hp.choice('CTriad', [0, 1]),
			 'KSCTriad': hp.choice('KSCTriad', [0, 1]),
			 'Global': hp.choice('Global', [0, 1]),
			 'Peptide': hp.choice('Peptide', [0, 1]),
			 'Fourier_Integer': hp.choice('Fourier_Integer', [0, 1]),
			 'Fourier_EIIP': hp.choice('Fourier_EIIP', [0, 1]),
			 'EIIP': hp.choice('EIIP', [0, 1]),
			 'AAAF': hp.choice('AAAF', [0, 1]),
			 'Classifier': hp.choice('Classifier', [0, 1, 2, 3])}

	trials = Trials()
	best_tuning = fmin(fn=objective_rf,
				space=space,
				algo=tpe.suggest,
				max_evals=estimations,
				trials=trials)

	# print(space)

	position = int((len(df_x.columns) - 5046) / 2)
	index = list()
	descriptors = {'Shannon': list(range(0, 5)), 'Tsallis_23': list(range(5, 10)),
				   'Tsallis_30': list(range(10, 15)), 'Tsallis_40': list(range(15, 20)),
				   'ComplexNetworks': list(range(20, 98)), 'kGap_di': list(range(98, 498)),
				   'AAC': list(range(498, 518)),
				   'DPC': list(range(518, 918)),
				   'CKSAAP': list(range(918, 3318)), 
			 	   'DDE': list(range(3318, 3718)),
			 	   'GAAC': list(range(3718, 3723)),
			 	   'CKSAAGP': list(range(3723, 3873)),
			 	   'GDPC': list(range(3873, 3898)),
			 	   'GTPC': list(range(3898, 4023)),
			 	   'CTDC': list(range(4023, 4062)),
			 	   'CTDT': list(range(4062, 4101)),
			 	   'CTDD': list(range(4101, 4296)),
			 	   'CTriad': list(range(4296, 4639)),
			 	   'KSCTriad': list(range(4639, 4982)), 
				   'Global': list(range(4982, 4992)),
				   'Peptide': list(range(4992, 5008)),
				   'Fourier_Integer': list(range(5008, 5027)),
				   'Fourier_EIIP': list(range(5027, 5046)),
				   'EIIP': list(range(5046, (5046 + position))),
				   'AAAF': list(range((5046 + position), len(df_x.columns)))} 

	for descriptor, ind in descriptors.items():
		result = param[descriptor][best_tuning[descriptor]]
		if result == 1:
			index = index + ind

	classifier = param['Classifier'][best_tuning['Classifier']]

	path_index = path_bio + '/index_best_descriptors.json'
	with open(path_index, 'a') as fp:
		json.dump(index, fp)
		print('Done writing JSON data into .json file - Best descriptors!')

	btrain = df_x.iloc[:, index]
	path_btrain = path_bio + '/best_train.csv'
	btrain.to_csv(path_btrain, index=False, header=True)

	if test != '':
		btest = df_test.iloc[:, index]
		path_btest = path_bio + '/best_test.csv'
		btest.to_csv(path_btest, index=False, header=True)
	else:
		btest, path_btest = '', ''

	return classifier, path_btrain, path_btest, btrain, btest


def feature_extraction(ftrain, ftrain_labels, ftest, ftest_labels, features, foutput):

	"""Extracts the features from the sequences in the fasta files."""

	path = foutput + '/feat_extraction'
	path_results = foutput

	try:
		shutil.rmtree(path)
		shutil.rmtree(path_results)
	except OSError as e:
		print("Error: %s - %s." % (e.filename, e.strerror))
		print('Creating Directory...')

	if not os.path.exists(path_results):
		os.mkdir(path_results)

	if not os.path.exists(path):
		os.mkdir(path)
		os.mkdir(path + '/train')
		os.mkdir(path + '/test')

	labels = [ftrain_labels]
	fasta = [ftrain]
	train_size = 0

	if fasta_test:
		labels.append(ftest_labels)
		fasta.append(ftest)

	datasets = []
	fasta_list = []

	print('Extracting features with MathFeature and iFeature...')

	for i in range(len(labels)):
		for j in range(len(labels[i])):
			file = fasta[i][j].split('/')[-1]
			if i == 0:  # Train
				preprocessed_fasta = path + '/train/pre_' + file
				subprocess.run(['python', 'other-methods/preprocessing.py',
								'-i', fasta[i][j], '-o', preprocessed_fasta],
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				train_size += len([1 for line in open(preprocessed_fasta) if line.startswith(">")])
			else:  # Test
				preprocessed_fasta = path + '/test/pre_' + file
				subprocess.run(['python', 'other-methods/preprocessing.py',
								'-i', fasta[i][j], '-o', preprocessed_fasta],
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

			fasta_list.append(preprocessed_fasta)

			if 1 in features:
				dataset = path + '/Shannon.csv'
				subprocess.run(['python', 'MathFeature/methods/EntropyClass.py',
								'-i', preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-k', '5', '-e', 'Shannon'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 2 in features:
				dataset = path + '/Tsallis_23.csv'
				subprocess.run(['python', 'other-methods/TsallisEntropy.py',
								'-i', preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-k', '5', '-q', '2.3'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 3 in features:
				dataset = path + '/Tsallis_30.csv'
				subprocess.run(['python', 'other-methods/TsallisEntropy.py',
								'-i', preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-k', '5', '-q', '3.0'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 4 in features:
				dataset = path + '/Tsallis_40.csv'
				subprocess.run(['python', 'other-methods/TsallisEntropy.py',
								'-i', preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-k', '5', '-q', '4.0'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 5 in features:
				dataset = path + '/ComplexNetworks.csv'
				subprocess.run(['python', 'MathFeature/methods/ComplexNetworksClass-v2.py', '-i',
								preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-k', '3'], stdout=subprocess.DEVNULL,
								stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 6 in features:
				dataset_di = path + '/kGap_di.csv'

				subprocess.run(['python', 'MathFeature/methods/Kgap.py', '-i',
								preprocessed_fasta, '-o', dataset_di, '-l',
								labels[i][j], '-k', '1', '-bef', '1',
								'-aft', '1', '-seq', '3'],
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset_di)

			if 7 in features:
				dataset = path + '/AAC.csv'
				subprocess.run(['python', 'other-methods/ExtractionTechniques-Protein.py', '-i',
								preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-t', 'AAC'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 8 in features:
				dataset = path + '/DPC.csv'
				subprocess.run(['python', 'other-methods/ExtractionTechniques-Protein.py', '-i',
								preprocessed_fasta, '-o', dataset, '-l', labels[i][j],
								'-t', 'DPC'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)


			if 9 in features:
				dataset = path + '/iFeature-features.csv'
				subprocess.run(['python', 'other-methods/iFeature-modified/iFeature.py', '--file',
								preprocessed_fasta, '--type', 'All', '--label', labels[i][j], '--out', dataset], 
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
				datasets.append(dataset)

			if 10 in features:
				try:
					dataset = path + '/Global.csv'
					subprocess.run(['python', 'other-methods/modlAMP-modified/descriptors.py', '-option',
								'global', '-label', labels[i][j], '-input', preprocessed_fasta, '-output', dataset], 
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
					datasets.append(dataset)
				except:
					pass

			if 11 in features:
				try:
					dataset = path + '/Peptide.csv'
					subprocess.run(['python', 'other-methods/modlAMP-modified/descriptors.py', '-option',
								'peptide', '-label', labels[i][j], '-input', preprocessed_fasta, '-output', dataset], 
								stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
					datasets.append(dataset)
				except:
					pass

	if 12 in features:
		dataset = path + '/Fourier_Integer.csv'
		if fasta_test:
			labels_list = ftrain_labels + ftest_labels
		else:
			labels_list = ftrain_labels
		text_input = ''
		for i in range(len(fasta_list)):
			text_input += fasta_list[i] + '\n' + labels_list[i] + '\n'

		subprocess.run(['python', 'MathFeature/methods/Mappings-Protein.py',
						'-n', str(len(fasta_list)), '-o',
						dataset, '-r', '6'], text=True, input=text_input,
					   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

		with open(dataset, 'r') as temp_f:
			col_count = [len(l.split(",")) for l in temp_f.readlines()]

		colnames = ['Integer_Fourier_' + str(i) for i in range(0, max(col_count))]

		df = pd.read_csv(dataset, names=colnames, header=0)
		df.rename(columns={df.columns[0]: 'nameseq', df.columns[-1]: 'label'}, inplace=True)
		df.to_csv(dataset, index=False)
		datasets.append(dataset)

	if 13 in features:
		dataset = path + '/Fourier_EIIP.csv'
		if fasta_test:
			labels_list = ftrain_labels + ftest_labels
		else:
			labels_list = ftrain_labels
		text_input = ''
		for i in range(len(fasta_list)):
			text_input += fasta_list[i] + '\n' + labels_list[i] + '\n'

		subprocess.run(['python', 'MathFeature/methods/Mappings-Protein.py',
						'-n', str(len(fasta_list)), '-o',
						dataset, '-r', '8'], text=True, input=text_input,
					   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

		with open(dataset, 'r') as temp_f:
			col_count = [len(l.split(",")) for l in temp_f.readlines()]

		colnames = ['EIIP_Fourier_' + str(i) for i in range(0, max(col_count))]

		df = pd.read_csv(dataset, names=colnames, header=0)
		df.rename(columns={df.columns[0]: 'nameseq', df.columns[-1]: 'label'}, inplace=True)
		df.to_csv(dataset, index=False)
		datasets.append(dataset)

	if 14 in features:
		dataset = path + '/EIIP.csv'
		if fasta_test:
			labels_list = ftrain_labels + ftest_labels
		else:
			labels_list = ftrain_labels
		text_input = ''
		for i in range(len(fasta_list)):
			text_input += fasta_list[i] + '\n' + labels_list[i] + '\n'

		subprocess.run(['python', 'MathFeature/methods/Mappings-Protein.py',
						'-n', str(len(fasta_list)), '-o',
						dataset, '-r', '7'], text=True, input=text_input,
					   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

		with open(dataset, 'r') as temp_f:
			col_count = [len(l.split(",")) for l in temp_f.readlines()]

		colnames = ['EIIP_' + str(i) for i in range(0, max(col_count))]

		df = pd.read_csv(dataset, names=colnames, header=None)
		df.rename(columns={df.columns[0]: 'nameseq', df.columns[-1]: 'label'}, inplace=True)
		df.to_csv(dataset, index=False)
		datasets.append(dataset)

	if 15 in features:
		dataset = path + '/AAAF.csv'
		if fasta_test:
			labels_list = ftrain_labels + ftest_labels
		else:
			labels_list = ftrain_labels
		text_input = ''
		for i in range(len(fasta_list)):
			text_input += fasta_list[i] + '\n' + labels_list[i] + '\n'

		subprocess.run(['python', 'MathFeature/methods/Mappings-Protein.py',
						'-n', str(len(fasta_list)), '-o',
						dataset, '-r', '1'], text=True, input=text_input,
					   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

		with open(dataset, 'r') as temp_f:
			col_count = [len(l.split(",")) for l in temp_f.readlines()]

		colnames = ['AccumulatedFrequency_' + str(i) for i in range(0, max(col_count))]

		df = pd.read_csv(dataset, names=colnames, header=None)
		df.rename(columns={df.columns[0]: 'nameseq', df.columns[-1]: 'label'}, inplace=True)
		df.to_csv(dataset, index=False)
		datasets.append(dataset)

	"""Concatenating all the extracted features"""

	if datasets:
		datasets = list(dict.fromkeys(datasets))
		dataframes = pd.concat([pd.read_csv(f) for f in datasets], axis=1)
		dataframes = dataframes.loc[:, ~dataframes.columns.duplicated()]
		dataframes = dataframes[~dataframes.nameseq.str.contains("nameseq")]

	X_train = dataframes.iloc[:train_size, :]
	X_train.pop('nameseq')
	y_train = X_train.pop('label')
	ftrain = path + '/ftrain.csv'
	X_train = X_train.fillna(0)
	X_train.to_csv(ftrain, index=False)
	flabeltrain = path + '/flabeltrain.csv'
	y_train.to_csv(flabeltrain, index=False, header=True)
	
	fnameseqtest, ftest, flabeltest = '', '', ''

	if fasta_test:
		X_test = dataframes.iloc[train_size:, :]
		y_test = X_test.pop('label')
		nameseq_test = X_test.pop('nameseq')
		fnameseqtest = path + '/fnameseqtest.csv'
		nameseq_test.to_csv(fnameseqtest, index=False, header=True)
		ftest = path + '/ftest.csv'
		X_test = X_test.fillna(0)
		X_test.to_csv(ftest, index=False)
		flabeltest = path + '/flabeltest.csv'
		y_test.to_csv(flabeltest, index=False, header=True)

	return fnameseqtest, ftrain, flabeltrain, ftest, flabeltest

##########################################################################
##########################################################################


if __name__ == '__main__':
	print('\n')
	print('###################################################################################')
	print('###################################################################################')
	print('##########         BioAutoML- Automated Feature Engineering             ###########')
	print('##########              Author: Robson Parmezan Bonidia                 ###########')
	print('##########         WebPage: https://bonidia.github.io/website/          ###########')
	print('###################################################################################')
	print('###################################################################################')
	print('\n')
	parser = argparse.ArgumentParser()
	parser.add_argument('-fasta_train', '--fasta_train', nargs='+',
						help='fasta format file, e.g., fasta/positive_protein.fasta'
							 'fasta/lncRNA.fasta fasta/negative_protein.fasta')
	parser.add_argument('-fasta_label_train', '--fasta_label_train', nargs='+',
						help='labels for fasta files, e.g., positive negative')
	parser.add_argument('-fasta_test', '--fasta_test', nargs='+',
						help='fasta format file, e.g., fasta/positive_protein_test.fasta negative_protein_test.fasta')
	parser.add_argument('-fasta_label_test', '--fasta_label_test', nargs='+',
						help='labels for fasta files, e.g., positive negative')
	parser.add_argument('-estimations', '--estimations', default=70,
						help='number of estimations - BioAutoML - default = 50')
	parser.add_argument('-n_cpu', '--n_cpu', default=1, help='number of cpus - default = 1')
	parser.add_argument('-output', '--output', help='results directory, e.g., result/')

	args = parser.parse_args()
	fasta_train = args.fasta_train
	fasta_label_train = args.fasta_label_train
	fasta_test = args.fasta_test
	fasta_label_test = args.fasta_label_test
	estimations = int(args.estimations)
	n_cpu = int(args.n_cpu)
	foutput = str(args.output)

	for fasta in fasta_train:
		if os.path.exists(fasta) is True:
			print('Train - %s: Found File' % fasta)
		else:
			print('Train - %s: File not exists' % fasta)
			sys.exit()

	if fasta_test:
		for fasta in fasta_test:
			if os.path.exists(fasta) is True:
				print('Test - %s: Found File' % fasta)
			else:
				print('Test - %s: File not exists' % fasta)
				sys.exit()

	start_time = time.time()

	features = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

	fnameseqtest, ftrain, ftrain_labels, \
		ftest, ftest_labels = feature_extraction(fasta_train, fasta_label_train,
												 fasta_test, fasta_label_test, features, foutput)

	classifier, path_train, path_test, train_best, test_best = \
		feature_engineering(estimations, ftrain, ftrain_labels, ftest, foutput)

	cost = (time.time() - start_time) / 60
	print('Computation time - Pipeline - Automated Feature Engineering: %s minutes' % cost)

	if len(fasta_label_train) > 2:
		subprocess.run(['python', 'BioAutoML-multiclass.py', '-train', path_train,
						 '-train_label', ftrain_labels, '-test', path_test,
						 '-test_label', ftest_labels, '-test_nameseq',
						 fnameseqtest, '-nf', 'True', '-classifier', str(classifier),
						 '-n_cpu', str(n_cpu), '-output', foutput])
	else:
		subprocess.run(['python', 'BioAutoML-binary.py', '-train', path_train,
						 '-train_label', ftrain_labels, '-test', path_test, '-test_label',
						 ftest_labels, '-test_nameseq', fnameseqtest,
						 '-nf', 'True', '-fs', str(1), '-classifier', str(classifier), '-n_cpu', str(n_cpu),
						 '-output', foutput])

##########################################################################
##########################################################################
