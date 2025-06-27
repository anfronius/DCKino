import React from "react";
import "./index.css"; // Tailwind CSS
import movies from './data/movies.json';

export default function App() {
  return (
    <>
      <header className="w-full bg-zinc-800 shadow-md sticky top-0 z-50">
        <div className="w-full px-4 py-4">
          <h1 className="text-2xl font-bold text-center text-white">
            🎬 DC Kino Showtimes
          </h1>
        </div>
      </header>

      <main className="min-h-screen px-4 py-6">
        <div className="w-full">
          <div className="flex flex-col gap-6">
            {movies.map((movie, index) => (
              <div
                key={index}
                className="bg-zinc-800 rounded-2xl shadow-md flex flex-col sm:flex-row overflow-hidden w-full"
              >
                <div className="w-full sm:w-40 h-40 sm:h-auto bg-zinc-700 flex items-center justify-center text-sm text-zinc-300">
                  {movie.poster || 'Poster'}
                </div>
                <div className="p-4 flex flex-col justify-center w-full">
                  <div className="text-xl font-semibold mb-2">{movie.title}</div>
                  <div className="text-zinc-400 text-sm">Showing Date: {movie.date}</div>
                  <div className="text-zinc-400 text-sm">Location: {movie.location}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}