import { Header } from '@/components/layout/Header';
import { HomeView } from '@/views/HomeView';
import { Footer } from '@/components/layout/Footer';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50/50 to-white">
      <Header />
      <HomeView />
      <Footer />
    </div>
  );
}

export default App;
