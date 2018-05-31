import numpy as np
import torch
import torch.nn as nn




class NCM_classifier(nn.Module):
	
	# Initialize the classifier
	def __init__(self, features, classes, alpha=0.9):
		super(NCM_classifier, self).__init__()
		self.means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)				# Class Means
		self.running_means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)
		self.alpha=alpha			# Mean decay value
		self.features=features			# Input features
		self.classes=classes
		

	# Forward pass (x=features)
	def forward(self,x):
		means_reshaped=self.means.view(1,self.classes,self.features).expand(x.shape[0],self.classes,self.features)
		features_reshaped=x.view(-1,1,self.features).expand(x.shape[0],self.classes,self.features)
		diff=(features_reshaped-means_reshaped)**2
		cumulative_diff=diff.sum(dim=-1)

		return -cumulative_diff
			
	
	# Update centers (x=features, y=labels)
	def update_means(self,x,y):
		for i in torch.unique(y):				# For each label
			N,mean=self.compute_mean(x,y,i)	# Compute mean

			# If labels already in the set, just update holder, otherwise add it to the model
			if N==0:
				self.running_means.data[i,:]=self.means.data[i,:]
			else:
				self.running_means.data[i,:]=mean
		
		# Update means
		self.update()
	

	# Perform the update following the mean decay procedure
	def update(self):
		self.means.data=self.alpha*self.means.data+(1-self.alpha)*self.running_means



	# Compute mean by filtering the data of the same label
	def compute_mean(self,x,y,i):
		mask=(i==y).view(-1,1).float()
		mask=mask.cuda()
		N=mask.sum()
		if N==0:
			return N,0
		else:
			return N,(x.data*mask).sum(dim=0)/N



class incremental_NCM_classifier(nn.Module):
	
	# Initialize the classifier
	def __init__(self, features, classes, alpha=0.9):
		super(incremental_NCM_classifier, self).__init__()
		if classes==0:
			self.means=nn.Parameter(torch.zeros(1,features),requires_grad=False)				# Class Means
			self.running_means=nn.Parameter(torch.zeros(1,features),requires_grad=False)
			self.classes=1
		else: 
			self.means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)				# Class Means
			self.running_means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)
			self.classes=classes

		self.means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)				# Class Means
		self.running_means=nn.Parameter(torch.zeros(classes,features),requires_grad=False)
		self.alpha=alpha			# Mean decay value
		self.features=features			# Input features
		self.labels={}
		

	# Forward pass (x=features)
	def forward(self,x):
		means_reshaped=self.means.view(1,self.classes,self.features).expand(x.shape[0],self.classes,self.features)
		features_reshaped=x.view(-1,1,self.features).expand(x.shape[0],self.classes,self.features)
		diff=(features_reshaped-means_reshaped)**2
		cumulative_diff=diff.sum(dim=-1)

		return -cumulative_diff
			
	
	# Update centers (x=features, y=labels)
	def update_means(self,x,y):
		for i in torch.unique(y):				# For each label
			N,mean=self.compute_mean(x,y,i)	# Compute mean

			if i not in self.labels.keys():
				self.add_class(i)

			# If labels already in the set, just update holder, otherwise add it to the model
			if N==0:
				self.running_means.data[i,:]=self.means.data[i,:]
			else:
				self.running_means.data[i,:]=mean
		
		# Update means
		self.update()
	

	# Perform the update following the mean decay procedure
	def update(self):
		self.means.data=self.alpha*self.means.data+(1-self.alpha)*self.running_means



	# Compute mean by filtering the data of the same label
	def compute_mean(self,x,y,i):
		mask=(i==y).view(-1,1).float()
		mask=mask.cuda()
		N=mask.sum()
		if N==0:
			return N,0
		else:
			return N,(x.data*mask).sum(dim=0)/N



	def convert_labels(self,y):
		out=[]
		for i in y.data[:]:
				out.append(self.labels[i])
		return torch.Tensor(out).to(y.device)
	



	# Add a classi to the dataset, updating the labels indeces
	def add_class(self, index):
		if self.classes==1:
			continue
		device=self.means.data.device

		self.labels[self.classes]=index
		self.classes=self.classes+1

		self.means.data=torch.cat([self.means.data,torch.zeros(1,self.features).to(device)],dim=0)
		self.running_means.data=torch.cat([self.running_means.data,torch.zeros(1,self.features).to(device)],dim=0)



	# Add a classi to the dataset, updating the labels indeces
	def init_from_labels(self, y):
		for i in torch.unique(y):				# For each label
			if i not in self.labels.keys():
				self.add_class(i)








