import React, { useEffect, useState } from "react";
import "./index.css"; // Tailwind CSS
import movies from './data/movies.json';
import theaters from './data/theaters.json';
import { getPosterUrl } from './utils/tmdb';

// Group and condense movies by date, title, and theaterID
const groupedByDate = movies.reduce((acc, movie) => {
  const key = `${movie.title}|${movie.theaterID}`;
  if (!acc[movie.date]) acc[movie.date] = {};
  if (!acc[movie.date][key]) {
    acc[movie.date][key] = {
      ...movie,
      times: [movie.time]
    };
  } else {
    acc[movie.date][key].times.push(movie.time);
  }
  return acc;
}, {});

const theaterMap = Object.fromEntries(theaters.map(t => [t.theaterID, t]));

export default function App() {
  const [posters, setPosters] = useState({});

  useEffect(() => {
    const loadPosters = async () => {
      const results = {};
      const seen = new Set();
      for (const movie of movies) {
        const key = `${movie.title}|${movie.theaterID}`;
        if (!seen.has(key)) {
          seen.add(key);
          const url = await getPosterUrl(movie.title);
          if (url) results[movie.title] = url;
        }
      }
      setPosters(results);
    };
    loadPosters();
  }, []);

  // Calculate unique movie-theater combinations
  const uniqueMovieKeys = new Set(movies.map(m => `${m.title}|${m.theaterID}`));

  // Log unique movie titles to confirm
  useEffect(() => {
    const uniqueTitles = new Set(movies.map(m => m.title));
    console.log("Unique movie titles:", Array.from(uniqueTitles));
  }, []);

  return (
    <>
      <header className="w-full bg-zinc-800 shadow-md sticky top-0 z-50">
        <div className="w-full px-4 py-4">
          <h1 className="text-4xl font-bold text-center text-white font-bungee">
            🎬 DC Kino Showtimes
          </h1>
        </div>
      </header>

      <header className="w-full bg-zinc-700 shadow-inner">
        <div className="w-full px-4 py-3 text-white text-center text-sm sm:text-base font-audiowide">
          <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-6">
            <span>🎞️ {uniqueMovieKeys.size} movies showing</span>
            <span>•</span>
            <span>🏛️ {Object.keys(theaterMap).length} theaters listed</span>
            <span>•</span>
            <span>
              🔌{" "}
              {theaters.some(theater => theater.online === false)
                ? "Some theater sites offline"
                : "All theater sites online"}
            </span>
          </div>
        </div>
      </header>

      <main className="min-h-screen px-4 py-6">
        <div className="w-full">
          <div className="flex flex-col gap-10">
            {Object.entries(groupedByDate).map(([date, showingsMap]) => {
              const groupedShowings = Object.values(showingsMap);
              return (
                <div key={date} className="flex flex-col gap-4">
                  <h2 className="text-4xl font-bold text-white border-b border-zinc-600 pb-2 font-montserratalts">
                    {date}
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {groupedShowings.map((movie, index) => {
                      const theater = theaterMap[movie.theaterID];
                      const bgClass = theater?.colorClass || 'bg-zinc-800';
                      const posterUrl = posters[movie.title];

                      return (
                        <div
                          key={index}
                          className="relative rounded-2xl shadow-lg flex flex-col sm:flex-row overflow-hidden h-60 transition-transform duration-300 transform hover:scale-[1.03] hover:shadow-2xl"
                        >
                          <div className="w-full sm:w-1/2 h-1/2 sm:h-full bg-zinc-700 flex items-center justify-center text-sm text-zinc-300 z-10">
                            {posterUrl ? (
                              <img src={posterUrl} alt={movie.title} className="object-cover w-full h-full" />
                            ) : (
                              movie.poster || 'Poster'
                            )}
                          </div>
                          {/* Background Layer */}
                          <div className={`absolute inset-0 ${bgClass} filter brightness-75`} />

                          {/* Content Layer */}
                          <div className="relative z-10 p-6 flex flex-col justify-start w-full text-white">
                            <div className="text-2xl font-semibold mt-1 mb-4 font-limelight line-clamp-3">{movie.title}</div>
                            <div className="mt-auto">
                              <div className="text-zinc-100 text-sm leading-tight mb-3 font-montserratalts">{movie.times.join(" • ")}</div>
                              <div className="text-zinc-100 text-xl font-alumnisc line-clamp-2">{theater?.name || 'Unknown Theater'}</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </>
  );
}
