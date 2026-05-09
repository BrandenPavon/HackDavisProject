import { useState, useEffect } from 'react';
import { Play, Check } from 'lucide-react';
import PainTracker from './PainTracker';

interface Exercise {
  id: string;
  name: string;
  sets: number;
  reps: string;
  duration?: string;
  instructions: string[];
  category: string;
  completed: boolean;
}

interface ExercisesProps {
  onStatusChange?: (hasIncomplete: boolean) => void;
}

export default function Exercises({ onStatusChange }: ExercisesProps) {
  const [activeExerciseId, setActiveExerciseId] = useState<string | null>(null);
  const [painLogged, setPainLogged] = useState(false);
  const [exercises, setExercises] = useState<Exercise[]>([
    {
      id: '1',
      name: 'Wrist Flexion Stretch',
      sets: 3,
      reps: '30 seconds',
      category: 'Flexibility',
      completed: true,
      instructions: [
        'Extend your arm in front with palm facing down',
        'Use your other hand to gently pull fingers down',
        'You should feel a stretch on top of your wrist',
        'Hold for 30 seconds',
        'Repeat with the other wrist',
      ],
    },
    {
      id: '2',
      name: 'Wrist Curls',
      sets: 3,
      reps: '15 reps',
      category: 'Strength',
      completed: true,
      instructions: [
        'Sit with your forearm resting on your thigh, palm up',
        'Hold a light weight (1-2 lbs) in your hand',
        'Slowly curl your wrist upward',
        'Lower back down with control',
        'Repeat and then switch hands',
      ],
    },
    {
      id: '3',
      name: 'Wrist Rotations',
      sets: 2,
      reps: '10 circles each direction',
      category: 'Mobility',
      completed: false,
      instructions: [
        'Extend your arm with a loose fist',
        'Slowly rotate your wrist in circles',
        'Complete 10 circles clockwise',
        'Then complete 10 circles counterclockwise',
        'Repeat with the other wrist',
      ],
    },
  ]);

  const toggleComplete = (id: string) => {
    setExercises(
      exercises.map((ex) =>
        ex.id === id ? { ...ex, completed: !ex.completed } : ex
      )
    );
  };

  const completedCount = exercises.filter((ex) => ex.completed).length;

  useEffect(() => {
    const allExercisesComplete = completedCount === exercises.length;
    const hasIncomplete = !allExercisesComplete || !painLogged;
    onStatusChange?.(hasIncomplete);
  }, [completedCount, exercises.length, painLogged, onStatusChange]);

  const exerciseImages: { [key: string]: string } = {
    '1': 'https://images.unsplash.com/photo-1728894703338-f48301458fa2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800',
    '2': 'https://images.unsplash.com/photo-1627738641656-aebd944716cb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800',
    '3': 'https://images.unsplash.com/photo-1734688680877-277057fbe97f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=800',
  };

  const activeExercise = exercises.find((ex) => ex.id === activeExerciseId);

  if (activeExercise) {
    return (
      <div className="p-4 space-y-4">
        {/* Back Button */}
        <button
          onClick={() => setActiveExerciseId(null)}
          className="w-full bg-gradient-to-r from-gray-600 to-gray-700 text-white py-3 px-6 rounded-xl font-semibold flex items-center justify-center gap-3 hover:from-gray-700 hover:to-gray-800 transition-all shadow-lg"
        >
          Back to Exercises
        </button>

        {/* Exercise Demonstration */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Exercise Image */}
          <div className="w-full h-64 bg-gray-200">
            <img
              src={exerciseImages[activeExercise.id]}
              alt={activeExercise.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Exercise Info */}
          <div className="p-4">
            <h3 className="font-semibold text-xl mb-2">{activeExercise.name}</h3>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                {activeExercise.category}
              </span>
              <span className="text-sm text-gray-600">
                {activeExercise.sets} sets × {activeExercise.reps}
              </span>
            </div>

            {/* Instructions */}
            <div className="mb-4">
              <h4 className="font-medium text-gray-900 mb-3">
                Instructions:
              </h4>
              <ol className="space-y-2">
                {activeExercise.instructions.map((instruction, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-600 flex gap-2"
                  >
                    <span className="text-blue-600 font-medium">
                      {index + 1}.
                    </span>
                    <span>{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Complete Exercise Button */}
            <button
              onClick={() => {
                toggleComplete(activeExercise.id);
                setActiveExerciseId(null);
              }}
              className={`w-full py-3 px-4 rounded-lg font-semibold transition-colors ${
                activeExercise.completed
                  ? 'bg-green-100 text-green-700 border-2 border-green-500'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {activeExercise.completed ? (
                <span className="flex items-center justify-center gap-2">
                  <Check className="w-5 h-5" />
                  Completed
                </span>
              ) : (
                'Mark as Complete'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg p-4 shadow">
        <h2 className="text-lg font-semibold mb-2">Today's Exercises</h2>
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {completedCount} of {exercises.length} completed
          </p>
          <div className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
            {Math.round((completedCount / exercises.length) * 100)}%
          </div>
        </div>
        <div className="mt-3 bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${(completedCount / exercises.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Exercise List */}
      <div className="space-y-3">
        {exercises.map((exercise) => (
          <div
            key={exercise.id}
            className={`bg-white rounded-lg shadow ${
              exercise.completed ? 'opacity-75' : ''
            }`}
          >
            <div className="p-4">
              <div className="flex items-start gap-3 mb-3">
                <button
                  onClick={() => toggleComplete(exercise.id)}
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 ${
                    exercise.completed
                      ? 'bg-green-500 border-green-500'
                      : 'border-gray-300'
                  }`}
                >
                  {exercise.completed && (
                    <Check className="w-4 h-4 text-white" />
                  )}
                </button>
                <div className="flex-1">
                  <h3
                    className={`font-medium ${
                      exercise.completed
                        ? 'line-through text-gray-500'
                        : 'text-gray-900'
                    }`}
                  >
                    {exercise.name}
                  </h3>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-sm text-gray-600">
                      {exercise.sets} sets × {exercise.reps}
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                      {exercise.category}
                    </span>
                  </div>
                </div>
              </div>

              {/* Start Exercise Button */}
              <button
                onClick={() => setActiveExerciseId(exercise.id)}
                className={`w-full py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                  exercise.completed
                    ? 'bg-green-100 text-green-700 border-2 border-green-500'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {exercise.completed ? (
                  <>
                    <Check className="w-4 h-4" />
                    Completed
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Start Exercise
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pain Tracker */}
      <PainTracker onPainLogged={() => setPainLogged(true)} />
    </div>
  );
}
