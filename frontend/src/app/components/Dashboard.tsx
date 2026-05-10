import { CheckCircle, AlertCircle, Clock, Flame } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="p-4 space-y-4">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h2 className="text-lg font-semibold mb-1">Welcome back, Sarah!</h2>
        <p className="text-sm text-gray-600">Keep up the great work on your recovery journey</p>
      </div>

      {/* Streak Feature - Emphasized */}
      <div className="bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12" />
        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Flame className="w-8 h-8 text-yellow-300 drop-shadow-lg" />
              <span className="text-white/90 font-medium">Current Streak</span>
            </div>
            <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full">
              <span className="text-white text-xs font-semibold">🏆 Keep Going!</span>
            </div>
          </div>
          <div className="flex items-end gap-2 mb-3">
            <span className="text-6xl font-bold text-white drop-shadow-lg">7</span>
            <span className="text-2xl text-white/90 mb-2">days</span>
          </div>
          <p className="text-white/90 text-sm mb-4">
            Amazing! You're on a roll. Complete today's exercises to reach 8 days!
          </p>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6, 7].map((day) => (
              <div
                key={day}
                className="flex-1 h-2 bg-white/30 rounded-full overflow-hidden"
              >
                <div className="h-full bg-yellow-300 rounded-full" />
              </div>
            ))}
            <div className="flex-1 h-2 bg-white/30 rounded-full" />
          </div>
        </div>
      </div>

      {/* Today's Exercises */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold mb-3">Today's Exercises</h3>
        <div className="space-y-3">
          <ExerciseItem
            title="Wrist Flexion Stretch"
            sets="3 sets × 30 sec"
            completed={true}
          />
          <ExerciseItem
            title="Wrist Curls"
            sets="3 sets × 15 reps"
            completed={true}
          />
          <ExerciseItem
            title="Wrist Rotations"
            sets="2 sets × 10 circles"
            completed={false}
          />
        </div>
      </div>

      {/* Next Appointment */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-4 shadow">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm opacity-90">Next Appointment</p>
            <p className="font-semibold mt-1">Dr. Johnson - Hand & Wrist Specialist</p>
            <p className="text-sm">Monday, May 12 at 2:00 PM</p>
          </div>
          <Clock className="w-8 h-8 opacity-80" />
        </div>
      </div>
    </div>
  );
}

function ExerciseItem({ title, sets, completed }: { title: string; sets: string; completed: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
          completed ? 'bg-green-100' : 'bg-gray-100'
        }`}>
          <CheckCircle className={`w-5 h-5 ${
            completed ? 'text-green-600' : 'text-gray-400'
          }`} />
        </div>
        <div>
          <p className={`text-sm font-medium ${completed ? 'text-gray-500 line-through' : ''}`}>
            {title}
          </p>
          <p className="text-xs text-gray-500">{sets}</p>
        </div>
      </div>
    </div>
  );
}
