<template>
  <div id="overview">
    <div class="section-hero text-center">
      <h1 class="main-title">
        Timely and quality feedback for large online courses
      </h1>
      <h2 class="sub-title">
        A better student experience for online higher-education
      </h2>
      <a class="btn btn-primary btn-lg mr-2" href="/users/login/">Login</a>
      <button v-scroll-to="'#how-it-works'" class="btn btn-primary btn-lg">
        Show me
      </button>
    </div>
    <div class="columns">
      <div class="column col-4 col-xs-12">
        <div class="card text-center">
          <div class="card-header">
            <img src="../assets/teacher-maths-female.svg" alt="" />
            <h4 class="card-title">Improve Education</h4>
          </div>
          <div class="card-body">
            <a href="https://eric.ed.gov/?q=nicol+AND+david&id=EJ1025819">
              Research
            </a>
            has shown the numerous pedagogical benefits of peer reviewing for
            students.
          </div>
        </div>
      </div>
      <div class="column col-4 col-xs-12">
        <div class="card text-center">
          <div class="card-header">
            <img src="../assets/robot-hand.svg" alt="" />
            <h4 class="card-title">Authentic Feedback</h4>
          </div>
          <div class="card-body">
            Encourage students to provide useful feedback with the help of our
            AI feedback evaluator.
          </div>
        </div>
      </div>
      <div class="column col-4 col-xs-12">
        <div class="card text-center">
          <div class="card-header">
            <img src="../assets/ecology-globe.svg" alt="" />
            <h4 class="card-title">Foster Collaboration</h4>
          </div>
          <div class="card-body">
            Help students collaborate to improve each others' assingments and to
            become active participants.
          </div>
        </div>
      </div>
      <div class="column col-12 text-center">
        <button
          v-scroll-to="'#how-it-works'"
          class="btn btn-primary btn-action btn-lg btn-scroll"
        >
          <i class="icon icon-downward"></i>
        </button>
      </div>
    </div>
    <div class="section section-features bg-primary text-light text-center">
      <div class="container grid-lg">
        <h3>Collaborative learning through Peer Feedback</h3>
        <p>
          Automatically turn assignments into a "poster session". A place for
          your students to present and discuss their assignments.
        </p>
        <how-it-works id="how-it-works"></how-it-works>
      </div>
    </div>
    <div class="columns">
      <div class="column col-6 col-xs-12">
        <h3>One click setup. Don't repeat yourself.</h3>
        <p>
          Built from the ground up with
          <a href="https://www.canvaslms.com/">Canvas LMS</a> in mind. Peer
          Feedback automatically imports all necessary data from Canvas.
        </p>
      </div>
      <div class="column col-6 col-xs-12">
        <img
          class="img-responsive img-heading"
          src="../assets/magician-male.svg"
          alt=""
        />
      </div>
    </div>
    <div class="columns">
      <div class="column col-6 col-xs-12">
        <img
          class="img-responsive img-heading"
          src="../assets/customer-service-man.svg"
          alt=""
        />
      </div>
      <div class="column col-6 col-xs-12">
        <h3>We have your back!</h3>
        <p>
          Count on our personalized support to help you implement Peer Feedback
          for your course. We will also solve any issues and answer all your
          questions.
        </p>
      </div>
    </div>
    <div class="section section-features bg-secondary text-center">
      <h3>
        Learn about how Georgia Tech's Online Master's in CS uses Peer Feedback
      </h3>
      <p>
        Over seven thousand students have used Peer Feedback to provide feedback
        to their peers.
      </p>
      <a
        href="mailto:gabriel@peerfeedback.io?subject=Peer Feedback at OMSCS"
        class="btn btn-primary my-2"
      >
        Tell me more
      </a>
    </div>
    <div class="columns">
      <div class="column col-6 col-xs-12">
        <h3>Based on research</h3>
        <p>Built in part on research that was developed at Georgia Tech.</p>
        <br />
        <p>
          <a
            href="http://lucylabs.gatech.edu/graders-as-meta-reviewers-simultaneously-scaling-and-improving-expert-evaluation-for-large-online-classrooms/"
          >
            Graders as Meta-Reviewers: Simultaneously Scaling and Improving
            Expert Evaluation for Large Online Classrooms
          </a>
        </p>
      </div>
      <div class="column col-6 col-xs-12">
        <img
          class="img-responsive img-heading"
          src="../assets/lab-scientist.svg"
          alt=""
        />
      </div>
    </div>
    <div class="section section-features bg-primary text-center">
      <div class="container grid-lg">
        <div class="columns">
          <div class="column col-6 col-xs-6">
            <h3>Ready to get started?</h3>
            <h4>Get in touch or create an account.</h4>
          </div>
          <div class="column col-6 col-xs-6">
            <a
              href="mailto:gabriel@peerfeedback.io?subject=Schedule a Peer Feedback Demo"
              class="btn mr-2"
            >
              Schedule a demo
            </a>
            <a class="btn" href="/users/login/">Login</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import HowItWorks from "../components/home/HowItWorks.vue"

export default {
  name: "HomePage",
  components: {
    HowItWorks
  }
}
</script>

<style scoped>
.btn-scroll {
  margin-top: 1.5rem;
}

.img-heading {
  max-width: 18rem;
}

.section-features {
  padding: 4.5rem 0.5rem;
}

@media (min-width: 500px) {
  .section {
    margin: 4.5rem 4.5rem;
    margin-left: calc(-100vw / 2 + 976px / 2);
    margin-right: calc(-100vw / 2 + 976px / 2);
  }
}

.section-hero {
  padding: 3.5rem 0.5rem;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 600;
}

.sub-title {
  margin-bottom: 2rem;
  font-size: 1.4rem;
  text-transform: initial;
  letter-spacing: 0.05rem;
}
</style>
