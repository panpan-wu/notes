package main

import (
	"flag"
	"os"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	vegeta "github.com/tsenart/vegeta/v12/lib"
)

// type Result struct {
// 	Attack    string        `json:"attack"`
// 	Seq       uint64        `json:"seq"`
// 	Code      uint16        `json:"code"`
// 	Timestamp time.Time     `json:"timestamp"`
// 	Latency   time.Duration `json:"latency"`
// 	BytesOut  uint64        `json:"bytes_out"`
// 	BytesIn   uint64        `json:"bytes_in"`
// 	Error     string        `json:"error"`
// 	Body      []byte        `json:"body"`
// 	Method    string        `json:"method"`
// 	URL       string        `json:"url"`
// 	Headers   http.Header   `json:"headers"`
// }

func main() {
	var addr string
	var duration int
	var num_workers int
	flag.StringVar(&addr, "addr", "ws://127.0.0.1:8000", "websocket addr")
	flag.IntVar(&duration, "duration", 60, "duration seconds")
	flag.IntVar(&num_workers, "num_workers", 1, "num_workers")
	flag.Parse()

	var handler Handler = &WSHandler{
		addr: addr,
	}

	attacker := NewAttacker(
		Workers(uint64(num_workers)),
		AttackerHandler(handler),
	)
	results := attacker.Attack(time.Duration(time.Duration(duration) * time.Second))
	enc := vegeta.NewEncoder(os.Stdout)
	for result := range results {
		if err := enc.Encode(result); err != nil {
			return
		}
	}
}

type Handler interface {
	Handle() ([]byte, error)
}

type WSHandler struct {
	addr string
}

func (h *WSHandler) Handle() ([]byte, error) {
	conn, _, err := websocket.DefaultDialer.Dial(h.addr, nil)
	if err != nil {
		return nil, err
	}
	defer func() {
		_ = conn.WriteControl(
			websocket.CloseMessage,
			websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""),
			time.Now().Add(10*time.Second))
		_ = conn.Close()
	}()
	err = conn.WriteMessage(websocket.TextMessage, []byte("hello world"))
	if err != nil {
		return nil, err
	}
	_, msg, err := conn.ReadMessage()
	if err != nil {
		return nil, err
	}
	return msg, nil
}

// Attacker is an attack executor which wraps an http.Client
type Attacker struct {
	stopch  chan struct{}
	workers uint64
	seqmu   sync.Mutex
	seq     uint64
	began   time.Time
	handler Handler
}

func NewAttacker(opts ...func(*Attacker)) *Attacker {
	a := &Attacker{
		stopch:  make(chan struct{}),
		workers: 1,
		began:   time.Now(),
	}

	for _, opt := range opts {
		opt(a)
	}

	return a
}

func Workers(n uint64) func(*Attacker) {
	return func(a *Attacker) { a.workers = n }
}

func AttackerHandler(handler Handler) func(*Attacker) {
	return func(a *Attacker) { a.handler = handler }
}

func (a *Attacker) Attack(du time.Duration) <-chan *vegeta.Result {
	var wg sync.WaitGroup

	workers := a.workers
	results := make(chan *vegeta.Result)
	ticks := make(chan struct{})
	for i := uint64(0); i < workers; i++ {
		wg.Add(1)
		go a.attack(&wg, ticks, results)
	}

	go func() {
		defer close(results)
		defer wg.Wait()
		defer close(ticks)

		began, count := time.Now(), uint64(0)
		for {
			elapsed := time.Since(began)
			if du > 0 && elapsed > du {
				return
			}

			select {
			case ticks <- struct{}{}:
				count++
			case <-a.stopch:
				return
			}
		}
	}()

	return results
}

func (a *Attacker) Stop() {
	select {
	case <-a.stopch:
		return
	default:
		close(a.stopch)
	}
}

func (a *Attacker) attack(workers *sync.WaitGroup, ticks <-chan struct{}, results chan<- *vegeta.Result) {
	defer workers.Done()
	for range ticks {
		results <- a.hit()
	}
}

func (a *Attacker) hit() *vegeta.Result {
	var (
		res = vegeta.Result{Attack: "websocket"}
		err error
	)

	a.seqmu.Lock()
	res.Timestamp = a.began.Add(time.Since(a.began))
	res.Seq = a.seq
	a.seq++
	a.seqmu.Unlock()

	defer func() {
		res.Latency = time.Since(res.Timestamp)
		if err != nil {
			res.Error = err.Error()
		}
	}()

	res.Method = "ws"
	res.URL = "url"
	res.Code = 200

	msg, err := a.handler.Handle()
	if err != nil {
		res.Error = err.Error()
		res.Code = 500
	} else {
		res.Body = msg
	}

	return &res
}
