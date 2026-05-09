import { Calendar, Clock, MapPin, Phone, Video, User } from 'lucide-react';

interface Appointment {
  id: string;
  doctor: string;
  specialty: string;
  date: string;
  time: string;
  location: string;
  type: 'in-person' | 'virtual';
  status: 'upcoming' | 'past';
}

export default function Appointments() {
  const appointments: Appointment[] = [
    {
      id: '1',
      doctor: 'Dr. Sarah Johnson',
      specialty: 'Hand & Wrist Specialist',
      date: 'Monday, May 12',
      time: '2:00 PM',
      location: 'Valley Medical Center',
      type: 'in-person',
      status: 'upcoming',
    },
    {
      id: '2',
      doctor: 'Dr. Michael Chen',
      specialty: 'Orthopedic Hand Surgeon',
      date: 'Friday, May 16',
      time: '10:30 AM',
      location: 'Virtual Consultation',
      type: 'virtual',
      status: 'upcoming',
    },
    {
      id: '3',
      doctor: 'Dr. Sarah Johnson',
      specialty: 'Hand & Wrist Specialist',
      date: 'Monday, May 5',
      time: '2:00 PM',
      location: 'Valley Medical Center',
      type: 'in-person',
      status: 'past',
    },
    {
      id: '4',
      doctor: 'Dr. Sarah Johnson',
      specialty: 'Hand & Wrist Specialist',
      date: 'Friday, May 2',
      time: '3:30 PM',
      location: 'Valley Medical Center',
      type: 'in-person',
      status: 'past',
    },
  ];

  const upcomingAppointments = appointments.filter((apt) => apt.status === 'upcoming');
  const pastAppointments = appointments.filter((apt) => apt.status === 'past');

  return (
    <div className="p-4 space-y-4">
      {/* Add Appointment Button */}
      <button className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors shadow">
        <Calendar className="w-5 h-5" />
        Schedule New Appointment
      </button>

      {/* Upcoming Appointments */}
      <div>
        <h2 className="font-semibold mb-3">Upcoming Appointments</h2>
        <div className="space-y-3">
          {upcomingAppointments.map((appointment) => (
            <AppointmentCard key={appointment.id} appointment={appointment} />
          ))}
        </div>
      </div>

      {/* Past Appointments */}
      <div>
        <h2 className="font-semibold mb-3">Past Appointments</h2>
        <div className="space-y-3">
          {pastAppointments.map((appointment) => (
            <AppointmentCard key={appointment.id} appointment={appointment} />
          ))}
        </div>
      </div>
    </div>
  );
}

function AppointmentCard({ appointment }: { appointment: Appointment }) {
  const isUpcoming = appointment.status === 'upcoming';

  return (
    <div className={`bg-white rounded-lg p-4 shadow ${!isUpcoming ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
            isUpcoming ? 'bg-blue-100' : 'bg-gray-100'
          }`}>
            <User className={`w-6 h-6 ${isUpcoming ? 'text-blue-600' : 'text-gray-400'}`} />
          </div>
          <div>
            <h3 className="font-semibold">{appointment.doctor}</h3>
            <p className="text-sm text-gray-600">{appointment.specialty}</p>
          </div>
        </div>
        {appointment.type === 'virtual' && (
          <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium flex items-center gap-1">
            <Video className="w-3 h-3" />
            Virtual
          </div>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Calendar className="w-4 h-4" />
          <span>{appointment.date}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Clock className="w-4 h-4" />
          <span>{appointment.time}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          {appointment.type === 'virtual' ? (
            <Video className="w-4 h-4" />
          ) : (
            <MapPin className="w-4 h-4" />
          )}
          <span>{appointment.location}</span>
        </div>
      </div>

      {isUpcoming && (
        <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
          {appointment.type === 'virtual' ? (
            <button className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg text-sm font-medium flex items-center justify-center gap-2 hover:bg-purple-700 transition-colors">
              <Video className="w-4 h-4" />
              Join Call
            </button>
          ) : (
            <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg text-sm font-medium flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors">
              <MapPin className="w-4 h-4" />
              Get Directions
            </button>
          )}
          <button className="bg-gray-100 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
            Reschedule
          </button>
        </div>
      )}
    </div>
  );
}
