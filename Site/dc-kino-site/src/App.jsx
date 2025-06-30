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

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-80 flex justify-center items-center">
      <div className="bg-zinc-800 text-white rounded-2xl shadow-xl p-6 max-w-xl w-full relative max-h-[80vh] overflow-y-auto">
        <button onClick={onClose} className="absolute top-2 right-2 text-white text-2xl">×</button>
        <h2 className="text-2xl mb-4 font-bungee text-center">{title}</h2>
        {children}
      </div>
    </div>
  );
}

export default function App() {
  const [posters, setPosters] = useState({});
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [showTheaterList, setShowTheaterList] = useState(false);
  const [showMovieList, setShowMovieList] = useState(false);
  const [showOfflineList, setShowOfflineList] = useState(false);

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

  const uniqueMovieKeys = new Set(movies.map(m => `${m.title}|${m.theaterID}`));
  const uniqueMovies = Array.from(new Set(movies.map(m => m.title)));
  const offlineTheaters = theaters.filter(theater => theater.online === false);

  return (
    <>
      <header className="w-full bg-zinc-800 shadow-md sticky top-0 z-50">
        <div className="w-full px-4 py-4 flex justify-between items-center">
          <button className="text-white material-icons text-base">menu</button>
          <h1 className="text-4xl font-bold text-center text-white font-bungee">
            🎬 DC Kino Showtimes
          </h1>
          <button className="text-white material-icons text-base">calendar_month</button>
        </div>
      </header>

      <header className="w-full bg-zinc-700 shadow-inner">
        <div className="w-full px-4 py-3 text-white text-center text-sm sm:text-base font-audiowide">
          <div className="flex flex-col sm:flex-row justify-center items-center gap-2 sm:gap-6">
            <button className="bg-zinc-800" onClick={() => setShowMovieList(true)}>
              🎞️ {uniqueMovieKeys.size} Movies Showing
            </button>
            <button className="bg-zinc-800" onClick={() => setShowTheaterList(true)}>
              🏛️ {Object.keys(theaterMap).length} Theaters Listed
            </button>
            <button className="bg-zinc-800" onClick={() => setShowOfflineList(true)}>
              🔌 {offlineTheaters.length > 0 ? `${offlineTheaters.length} Theater${offlineTheaters.length > 1 ? 's' : ''} Offline` : "All Theater Sites Online"}
            </button>
          </div>
        </div>
      </header>

      <main className="min-h-screen px-4 py-6 relative">
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
                          onClick={() => setSelectedMovie({ ...movie, bgClass })}
                          className="cursor-pointer relative rounded-2xl shadow-lg flex flex-col sm:flex-row overflow-hidden h-60 transition-transform duration-300 transform hover:scale-[1.03] hover:shadow-2xl"
                        >
                          <div className="w-full sm:w-1/2 h-1/2 sm:h-full bg-zinc-700 flex items-center justify-center text-sm text-zinc-300 z-10">
                            {posterUrl ? (
                              <img src={posterUrl} alt={movie.title} className="object-cover w-full h-full" />
                            ) : (
                              movie.poster || 'Poster'
                            )}
                          </div>
                          <div className={`absolute inset-0 ${bgClass} filter brightness-75`} />
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

        {/* Movie Modal Overlay */}
        {selectedMovie && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-80 flex justify-center items-center">
            <div className={`text-white rounded-2xl shadow-xl p-6 max-w-4xl w-full relative flex flex-col sm:flex-row gap-6 ${selectedMovie.bgClass}`}>
              <button onClick={() => setSelectedMovie(null)} className="absolute top-2 right-2 text-white text-2xl">×</button>
              <div className="sm:w-1/2 flex justify-center items-center">
                {posters[selectedMovie.title] ? (
                  <img src={posters[selectedMovie.title]} alt={selectedMovie.title} className="object-cover max-h-[500px] w-full rounded" />
                ) : (
                  <div className="bg-zinc-700 h-60 w-full flex items-center justify-center text-sm text-zinc-300">
                    {selectedMovie.poster || 'Poster Unavailable'}
                  </div>
                )}
              </div>
              <div className="sm:w-1/2 flex flex-col justify-center">
                <h2 className="text-3xl font-bold mb-4 font-limelight">{selectedMovie.title}</h2>
                <p className="text-zinc-300 mb-2 text-sm font-montserratalts">{selectedMovie.times.join(" • ")}</p>
                <p className="text-zinc-100 text-xl font-alumnisc mb-4">{theaterMap[selectedMovie.theaterID]?.name || 'Unknown Theater'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Theater List Modal */}
        {showTheaterList && (
          <Modal title="Theaters Listed" onClose={() => setShowTheaterList(false)}>
            <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
              {Object.values(theaterMap).map((theater, index) => (
                <li key={index}>{theater.name}</li>
              ))}
            </ul>
          </Modal>
        )}

        {/* Movie List Modal */}
        {showMovieList && (
          <Modal title="Movies Listed" onClose={() => setShowMovieList(false)}>
            <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
              {uniqueMovies.map((title, index) => (
                <li key={index}>{title}</li>
              ))}
            </ul>
          </Modal>
        )}

        {/* Offline Theater List Modal */}
        {showOfflineList && (
          <Modal title="Theater Status" onClose={() => setShowOfflineList(false)}>
            {offlineTheaters.length > 0 ? (
              <ul className="list-disc pl-6 space-y-2 text-sm font-audiowide">
                {offlineTheaters.map((theater, index) => (
                  <li key={index}>{theater.name}</li>
                ))}
              </ul>
            ) : (
              <p className="text-center text-sm font-audiowide">All theaters are currently online!</p>
            )}
          </Modal>
        )}
      </main>
    </>
  );
}
