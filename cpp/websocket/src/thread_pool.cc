#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>

#include <exception>
#include <future>
#include <iostream>

using namespace std;

class ThreadPool {
  private:
    boost::asio::thread_pool pool_;

  public:
    ThreadPool(int num_threads): pool_(num_threads) {}

    template<typename F>
    void Post(F&& f) {
      boost::asio::post(pool_, std::forward<F>(f));
    }

    template <typename F>
    auto Submit(F&& f) -> std::future<decltype(f())>
    {
      std::promise<decltype(f())> promise;
      auto future = promise.get_future();
      boost::asio::post(
        pool_,
        [promise = std::move(promise), f = std::forward<F>(f)] () mutable
        {
          try {
            auto value = f();
            promise.set_value(value);
          } catch (...) {
            promise.set_exception(std::current_exception());
          }
        }
      );
      return future;
    }

    template <typename F, typename C>
    void SubmitWithCallback(F&& f, C&& c)
    {
      boost::asio::post(
        pool_,
        [f = std::forward<F>(f), c = std::forward<C>(c)] () mutable
        {
          auto value = f();
          c(value);
        }
      );
    }

    void Join() {
      pool_.join();
    }
};

class Data {
  private:
    int data_;
  public:
    Data(int data): data_(data) {}
    int Mul() { return data_ * 10; }
    void Set(int data) { data_ = data; }
    int Get() { return data_; }
};

void test1() {
  // boost::asio::thread_pool pool(4); // 4 threads
  // boost::asio::post(pool, [] { cout << "hello" << endl; });
  // pool.join();

  ThreadPool pool(4);
  pool.Post([]{ cout << "hello 1" << endl; });
  auto future = pool.Submit([]{ return 10; });
  cout << "future: " << future.get() << endl;

  auto future1 = pool.Submit([]() -> int { throw "test exception"; return 11; });
  try {
    auto value = future1.get();
    cout << "future1: " << value << endl;
  } catch (const char* e) {
    cout << "future1 exception: " << e << endl;
  }

  pool.SubmitWithCallback(
    [](){ return 100; },
    [](int i){ cout << "callback: " << i << endl; }
  );

  pool.Join();
}

void test2() {
  ThreadPool pool(1);
  Data data(11);
  cout << "before: " << data.Get() << endl;
  pool.SubmitWithCallback(
      [&data]{ return data.Mul(); },
      [&data](int value){ data.Set(value); }
  );
  pool.Join();
  cout << "after: " << data.Get() << endl;
}

int main() {
  test2();

  return 0;
}
