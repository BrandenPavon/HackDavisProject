import { useState } from 'react';
import { Home, Activity, TrendingUp, Trophy, Menu } from 'lucide-react';
import Dashboard from './components/Dashboard';
import Exercises from './components/Exercises';
import Progress from './components/Progress';
import Leaderboard from './components/Leaderboard';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [hasIncompleteItems, setHasIncompleteItems] = useState(true);

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <Dashboard />;
      case 'exercises':
        return <Exercises onStatusChange={setHasIncompleteItems} />;
      case 'progress':
        return <Progress />;
      case 'leaderboard':
        return <Leaderboard />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="size-full flex items-center justify-center bg-gray-900">
      {/* Mobile Device Frame */}
      <div className="w-full max-w-[430px] h-full max-h-[932px] flex flex-col bg-gray-50 shadow-2xl relative">
        {/* Header */}
        <header className="bg-blue-600 text-white p-4 shadow-md">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold">PT Recovery</h1>
            <Menu className="w-6 h-6" />
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-20">
          {renderContent()}
        </main>

        {/* Bottom Navigation */}
        <nav className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
          <div className="flex justify-around items-center h-16">
            <button
              onClick={() => setActiveTab('home')}
              className={`flex flex-col items-center justify-center flex-1 h-full ${
                activeTab === 'home' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              <Home className="w-5 h-5" />
              <span className="text-xs mt-1">Home</span>
            </button>
            <button
              onClick={() => setActiveTab('exercises')}
              className={`flex flex-col items-center justify-center flex-1 h-full relative ${
                activeTab === 'exercises' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              {hasIncompleteItems && (
                <div className="absolute top-2 right-1/2 translate-x-3 w-2 h-2 bg-red-500 rounded-full" />
              )}
              <Activity className="w-5 h-5" />
              <span className="text-xs mt-1">Exercises</span>
            </button>
            <button
              onClick={() => setActiveTab('progress')}
              className={`flex flex-col items-center justify-center flex-1 h-full ${
                activeTab === 'progress' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
              <span className="text-xs mt-1">Progress</span>
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`flex flex-col items-center justify-center flex-1 h-full ${
                activeTab === 'leaderboard' ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              <Trophy className="w-5 h-5" />
              <span className="text-xs mt-1">Leaderboard</span>
            </button>
          </div>
        </nav>
      </div>
    </div>
  );
}
