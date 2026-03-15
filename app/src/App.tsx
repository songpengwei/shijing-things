import { Header } from '@/sections/Header';
import { MainContent } from '@/sections/MainContent';
import { Footer } from '@/sections/Footer';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50/50 to-white">
      <Header />
      <MainContent />
      <Footer />
    </div>
  );
}

export default App;
