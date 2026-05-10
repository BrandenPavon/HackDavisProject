import { Trophy, Medal, Flame, Crown } from 'lucide-react';

interface LeaderboardUser {
  id: string;
  name: string;
  avatar: string;
  streak: number;
  completionRate: number;
  totalExercises: number;
  painImprovement: number;
  isCurrentUser?: boolean;
}

export default function Leaderboard() {
  const users: LeaderboardUser[] = [
    {
      id: '1',
      name: 'Michael Rodriguez',
      avatar: '👨',
      streak: 21,
      completionRate: 98,
      totalExercises: 147,
      painImprovement: 65,
    },
    {
      id: '2',
      name: 'Emily Chen',
      avatar: '👩',
      streak: 14,
      completionRate: 95,
      totalExercises: 98,
      painImprovement: 58,
    },
    {
      id: '3',
      name: 'Sarah (You)',
      avatar: '👤',
      streak: 7,
      completionRate: 85,
      totalExercises: 56,
      painImprovement: 57,
      isCurrentUser: true,
    },
    {
      id: '4',
      name: 'James Wilson',
      avatar: '👨',
      streak: 5,
      completionRate: 82,
      totalExercises: 45,
      painImprovement: 42,
    },
    {
      id: '5',
      name: 'Lisa Anderson',
      avatar: '👩',
      streak: 4,
      completionRate: 78,
      totalExercises: 39,
      painImprovement: 38,
    },
    {
      id: '6',
      name: 'David Park',
      avatar: '👨',
      streak: 3,
      completionRate: 75,
      totalExercises: 32,
      painImprovement: 35,
    },
    {
      id: '7',
      name: 'Maria Garcia',
      avatar: '👩',
      streak: 3,
      completionRate: 72,
      totalExercises: 28,
      painImprovement: 31,
    },
  ];

  const sortedUsers = [...users].sort((a, b) => b.streak - a.streak);

  const currentUserRank = sortedUsers.findIndex((user) => user.isCurrentUser) + 1;

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Medal className="w-5 h-5 text-amber-600" />;
    return null;
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-400 to-yellow-600';
    if (rank === 2) return 'bg-gradient-to-r from-gray-300 to-gray-400';
    if (rank === 3) return 'bg-gradient-to-r from-amber-500 to-amber-700';
    return 'bg-gray-100';
  };

  return (
    <div className="p-4 space-y-4">
      {/* Your Rank Card */}
      <div className="bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white rounded-xl p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm opacity-90">Your Rank</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-4xl font-bold">#{currentUserRank}</span>
              {getRankIcon(currentUserRank) && (
                <div className="mt-2">{getRankIcon(currentUserRank)}</div>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center justify-end gap-2 mb-1">
              <Flame className="w-5 h-5" />
              <p className="text-sm opacity-90">Current Streak</p>
            </div>
            <p className="text-3xl font-bold">
              {users.find((u) => u.isCurrentUser)?.streak} days
            </p>
          </div>
        </div>
      </div>

      {/* Leaderboard List */}
      <div className="space-y-2">
        {sortedUsers.map((user, index) => {
          const rank = index + 1;
          return (
            <div
              key={user.id}
              className={`rounded-lg p-4 shadow transition-all ${
                user.isCurrentUser
                  ? 'bg-blue-50 border-2 border-blue-500'
                  : 'bg-white'
              } ${rank <= 3 ? 'shadow-md' : ''}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {/* Rank */}
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      rank <= 3
                        ? getRankBadge(rank) + ' text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {rank <= 3 ? getRankIcon(rank) : `#${rank}`}
                  </div>

                  {/* Avatar & Name */}
                  <div className="flex items-center gap-2">
                    <div className="text-2xl">{user.avatar}</div>
                    <div>
                      <p className={`font-medium ${user.isCurrentUser ? 'text-blue-700' : ''}`}>
                        {user.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {user.totalExercises} exercises completed
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stat */}
                <div className="text-right">
                  <div className="flex items-center gap-1">
                    <Flame className="w-4 h-4 text-orange-500" />
                    <p className="text-xl font-bold text-gray-900">
                      {user.streak} days
                    </p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Motivation Message */}
      <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Trophy className="w-6 h-6 text-purple-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-purple-900">Keep pushing!</p>
            <p className="text-sm text-purple-700 mt-1">
              {currentUserRank > 1
                ? `You're ${currentUserRank - 1} ${currentUserRank === 2 ? 'spot' : 'spots'} away from ${currentUserRank === 2 ? '1st place' : `#${currentUserRank - 1}`}. Stay consistent!`
                : "You're crushing it! Keep that #1 spot!"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
