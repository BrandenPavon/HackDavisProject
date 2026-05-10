import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingDown, Award, Target } from 'lucide-react';

const painData = [
  { date: 'May 3', level: 7 },
  { date: 'May 4', level: 6 },
  { date: 'May 5', level: 6 },
  { date: 'May 6', level: 5 },
  { date: 'May 7', level: 4 },
  { date: 'May 8', level: 4 },
  { date: 'May 9', level: 3 },
];

const exerciseCompletionData = [
  { day: 'Mon', completed: 8 },
  { day: 'Tue', completed: 7 },
  { day: 'Wed', completed: 9 },
  { day: 'Thu', completed: 6 },
  { day: 'Fri', completed: 8 },
  { day: 'Sat', completed: 10 },
  { day: 'Sun', completed: 9 },
];

export default function Progress() {
  return (
    <div className="p-4 space-y-4">
      {/* Overview Stats */}
      <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg p-4 shadow">
        <div className="flex items-center gap-3 mb-2">
          <TrendingDown className="w-6 h-6" />
          <h2 className="text-lg font-semibold">Great Progress!</h2>
        </div>
        <p className="text-sm opacity-90">
          Your wrist pain has decreased by 57% over the past week
        </p>
      </div>

      {/* Achievements */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold mb-3">Recent Achievements</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
              <Award className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="font-medium text-sm">7-Day Streak</p>
              <p className="text-xs text-gray-600">Completed exercises every day this week</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="font-medium text-sm">Weekly Goal Reached</p>
              <p className="text-xs text-gray-600">100% exercise completion this week</p>
            </div>
          </div>
        </div>
      </div>

      {/* Pain Level Trend */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold mb-3">Pain Level Trend</h3>
        <p className="text-sm text-gray-600 mb-4">Past 7 days</p>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={painData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <YAxis
              domain={[0, 10]}
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            <Line
              type="monotone"
              dataKey="level"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <div>
            <p className="text-xs text-gray-600">Current Level</p>
            <p className="text-2xl font-bold text-blue-600">3/10</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-600">Started At</p>
            <p className="text-2xl font-bold text-gray-400">7/10</p>
          </div>
        </div>
      </div>

      {/* Exercise Completion */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold mb-3">Exercise Completion</h3>
        <p className="text-sm text-gray-600 mb-4">This week</p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={exerciseCompletionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="day"
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#9ca3af"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px'
              }}
            />
            <Bar
              dataKey="completed"
              fill="#10b981"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">Weekly Average</p>
            <p className="text-lg font-bold text-green-600">8.1 exercises/day</p>
          </div>
        </div>
      </div>

      {/* Range of Motion */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h3 className="font-semibold mb-3">Range of Motion</h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Wrist Flexion</span>
              <span className="text-sm font-semibold">65°</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: '81%' }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Target: 80°</p>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Wrist Extension</span>
              <span className="text-sm font-semibold">60°</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: '86%' }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Target: 70°</p>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Grip Strength</span>
              <span className="text-sm font-semibold">18 lbs</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full"
                style={{ width: '72%' }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">Target: 25 lbs</p>
          </div>
        </div>
      </div>
    </div>
  );
}
