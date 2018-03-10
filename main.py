from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
from datetime import datetime
import webapp2
import json
import logging

def getEmail(token):
	try:
	    headers = {'Authorization': token}
	    result = urlfetch.fetch(
	        url = 'https://www.googleapis.com/oauth2/v2/userinfo',
	        method = urlfetch.GET,
	        headers = headers)
	    content = json.loads(result.content)
	    return content['email']
	except urlfetch.Error:
	    logging.exception('Caught exception fetching url')

class Patient(ndb.Model):
	user_email = ndb.StringProperty(required = True)
	name = ndb.StringProperty(required = True)
	age = ndb.IntegerProperty(required = True)
	weight = ndb.IntegerProperty(required = True)
	current_doctor = ndb.StringProperty()

class PatientHandler(webapp2.RequestHandler):
	def post(self):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
		
		patient_data = json.loads(self.request.body)

		if "name" not in patient_data or "age" not in patient_data or "weight" not in patient_data:
			self.response.write("Missing fields in post request")
			self.response.set_status(400)
		else:
			new_patient = Patient(	user_email = email,
									name = patient_data['name'],
									age = patient_data['age'],
									weight = patient_data['weight'],
									current_doctor = None	)
			new_patient.put()
			patient_dict = new_patient.to_dict()
			patient_dict['id'] = new_patient.key.urlsafe()
			patient_dict['self'] = '/patient/' + new_patient.key.urlsafe()
			self.response.write(json.dumps(patient_dict))
			self.response.set_status(201)

	def get(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
		
		if id:
			patient = None
			try:
				patient = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if patient:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				patient_dict['id'] = id
				patient_dict['self'] = '/patient/' + id
				self.response.write(json.dumps(patient_dict))
				self.response.set_status(200)
		else:
			all_patients = Patient.query().fetch(1000)
			patients = []
			for patient in all_patients:
				patient_dict = patient.to_dict()
				patient_dict['id'] = patient.key.urlsafe()
				patient_dict['self'] = '/patient/' + patient.key.urlsafe()
				
				if patient_dict['user_email'] == email:
					patients.append(patient_dict)

			self.response.write(json.dumps(patients))
			self.response.set_status(200)

	def delete(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			patient = None
			try:
				patient = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if patient:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				
				if patient_dict['current_doctor'] != None:
					doctor = ndb.Key(urlsafe = patient_dict['current_doctor']).get()
					doctor.patient_count -= 1
					doctor.put()
				
				patient.key.delete()
			else:
				self.response.write('Patient does not exist')
				self.response.set_status(404)
		else:
			patients = Patient.query().fetch(1000)
			for patient in patients:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] == email:
					if patient_dict['current_doctor'] != None:
						doctor = ndb.Key(urlsafe = patient_dict['current_doctor']).get()
						doctor.patient_count -= 1
						doctor.put()
					patient.key.delete()

	def patch(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			patient = None
			try:
				patient = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if patient:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				patient_data = json.loads(self.request.body)
				if 'name' in patient_data:
					patient.name = patient_data['name']
				if 'age' in patient_data:
					patient.age = patient_data['age']
				if 'weight' in patient_data:
					patient.weight = patient_data['weight']
				patient.put()
				patient_dict = patient.to_dict()
				patient_dict['id'] = patient.key.urlsafe()
				patient_dict['self'] = '/patient/' + patient.key.urlsafe()
				self.response.write(json.dumps(patient_dict))
			else:
				self.response.write('Patient does not exist')
				self.response.set_status(404)
		else:
			self.response.write('Patient id not provided')
			self.response.set_status(400)

class Doctor(ndb.Model):
	user_email = ndb.StringProperty(required = True)
	name = ndb.StringProperty(required = True)
	clinic = ndb.StringProperty(required = True)
	specialty = ndb.StringProperty(required = True)
	patient_count = ndb.IntegerProperty(required = True)

class DoctorHandler(webapp2.RequestHandler):
	def post(self):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
		
		doctor_data = json.loads(self.request.body)

		if "name" not in doctor_data or "clinic" not in doctor_data or "specialty" not in doctor_data:
			self.response.write("Missing fields in post request")
			self.response.set_status(400)
		else:
			new_doctor = Doctor(	user_email = email,
									name = doctor_data['name'],
									clinic = doctor_data['clinic'],
									specialty = doctor_data['specialty'],
									patient_count = 0	)
			new_doctor.put()
			doctor_dict = new_doctor.to_dict()
			doctor_dict['id'] = new_doctor.key.urlsafe()
			doctor_dict['self'] = '/doctor/' + new_doctor.key.urlsafe()
			self.response.write(json.dumps(doctor_dict))
			self.response.set_status(201)

	def get(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
		
		if id:
			doctor = None
			try:
				doctor = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if doctor:
				doctor_dict = doctor.to_dict()
				if doctor_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				doctor_dict['id'] = id
				doctor_dict['self'] = '/doctor/' + id
				self.response.write(json.dumps(doctor_dict))
				self.response.set_status(200)
		else:
			all_doctors = Doctor.query().fetch(1000)
			doctors = []
			for doctor in all_doctors:
				doctor_dict = doctor.to_dict()
				doctor_dict['id'] = doctor.key.urlsafe()
				doctor_dict['self'] = '/doctor/' + doctor.key.urlsafe()
				
				if doctor_dict['user_email'] == email:
					doctors.append(doctor_dict)

			self.response.write(json.dumps(doctors))
			self.response.set_status(200)

	def delete(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			doctor = None
			try:
				doctor = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if doctor:
				doctor_dict = doctor.to_dict()
				if doctor_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				
				if doctor_dict['patient_count'] > 0:
					patients = Patient.query(Patient.current_doctor == id).fetch(1000)
					for patient in patients:
						logging.critical(patient.current_doctor)
						patient.current_doctor = None
						logging.critical(patient.current_doctor)
						patient.put()
				
				doctor.key.delete()
			else:
				self.response.write('Doctor does not exist')
				self.response.set_status(404)
		else:
			doctors = Doctor.query().fetch(1000)
			for doctor in doctors:
				doctor_dict = doctor.to_dict()
				if doctor_dict['user_email'] == email:
					if doctor_dict['patient_count'] > 0:
						patients = Patient.query(Patient.current_doctor == doctor.key.urlsafe()).fetch(1000)
						for patient in patients:
							logging.critical(patient.current_doctor)
							patient.current_doctor = None
							logging.critical(patient.current_doctor)
							patient.put()
					doctor.key.delete()

	def patch(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			doctor = None
			try:
				doctor = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if doctor:
				doctor_dict = doctor.to_dict()
				if doctor_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				doctor_data = json.loads(self.request.body)
				if 'name' in doctor_data:
					doctor.name = doctor_data['name']
				if 'clinic' in doctor_data:
					doctor.clinic = doctor_data['clinic']
				if 'specialty' in doctor_data:
					doctor.specialty = doctor_data['specialty']
				doctor.put()
				doctor_dict = doctor.to_dict()
				doctor_dict['id'] = doctor.key.urlsafe()
				doctor_dict['self'] = '/doctor/' + doctor.key.urlsafe()
				self.response.write(json.dumps(doctor_dict))
			else:
				self.response.write('Doctor does not exist')
				self.response.set_status(404)
		else:
			self.response.write('Doctor id not provided')
			self.response.set_status(400)

class VisitHandler(webapp2.RequestHandler):
	def put(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			patient = None
			try:
				patient = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if patient and not patient.current_doctor:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				
				open_doctor = Doctor.query(Doctor.user_email == email).fetch(1)
				
				if open_doctor:
					doctor = open_doctor[0]
					data = []

					patient.current_doctor = doctor.key.urlsafe()
					patient.put()
					patient_dict = patient.to_dict()
					patient_dict['id'] = patient.key.urlsafe()
					patient_dict['self'] = '/patient/' + patient.key.urlsafe()
					data.append(patient_dict)

					doctor.patient_count += 1
					doctor.put()
					doctor_dict = doctor.to_dict()
					doctor_dict['id'] = doctor.key.urlsafe()
					doctor_dict['self'] = '/doctor/' + doctor.key.urlsafe()
					data.append(doctor_dict)

					self.response.write(json.dumps(data))
				else:
					self.response.write("Could not find any doctors")
					self.response.set_status(404)
					
			elif patient and patient.current_doctor:
				self.response.write("Patient is already assigned to a doctor")
				self.response.set_status(400)
			
			else:
				self.response.write("Patient not found")
				self.response.set_status(404)

	def delete(self, id = None):
		email = None
		if 'Authorization' in self.request.headers:
			email = getEmail(self.request.headers['Authorization'])
		else:
			self.response.write("Email not found for current user")
			self.response.set_status(400)
			return
			
		if id:
			patient = None
			try:
				patient = ndb.Key(urlsafe = id).get()
			except TypeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			except ProtocolBufferDecodeError:
				self.response.write('Invalid urlsafe string')
				self.response.set_status(404)
				return
			if patient and patient.current_doctor:
				patient_dict = patient.to_dict()
				if patient_dict['user_email'] != email:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
					
				doctor = None
				try:
					doctor = ndb.Key(urlsafe = patient.current_doctor).get()
				except TypeError:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
				except ProtocolBufferDecodeError:
					self.response.write('Invalid urlsafe string')
					self.response.set_status(404)
					return
					
				data = []

				patient.current_doctor = None
				patient.put()
				patient_dict = patient.to_dict()
				patient_dict['id'] = patient.key.urlsafe()
				patient_dict['self'] = '/patient/' + patient.key.urlsafe()
				data.append(patient_dict)

				doctor.patient_count -= 1
				doctor.put()
				doctor_dict = doctor.to_dict()
				doctor_dict['id'] = doctor.key.urlsafe()
				doctor_dict['self'] = '/doctor/' + doctor.key.urlsafe()
				data.append(doctor_dict)

				self.response.write(json.dumps(data))
				
			elif patient and not patient.current_doctor:
				self.response.write("Patient does not have a doctor to delete")
				self.response.set_status(400)
			
			else:
				self.response.write("Patient not found")
				self.response.set_status(404)

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Sam Keller - Cloud Final Project')

allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/patient', PatientHandler),
	('/patient/(.*)', PatientHandler),
	('/doctor', DoctorHandler),
	('/doctor/patient/(.*)', VisitHandler),
	('/doctor/(.*)', DoctorHandler),
], debug=True)
