import { expect } from "chai"

/* Helper for testing action with expected mutations */
export const testAction = (action, payload, state, expectedMutations, done) => {
  let count = 0

  // mock commit
  const commit = (type, payload) => {
    const mutation = expectedMutations[count]

    try {
      expect(type).to.equal(mutation.type)
      if (payload) {
        expect(payload).to.deep.equal(mutation.payload)
      }
    } catch (error) {
      console.error(error)
      done(error)
    }

    count++
    if (count >= expectedMutations.length) {
      done()
    }
  }

  // eslint-disable-next-line
  const dispatch = (type, payload, options) => {}

  // call the action with mocked store and arguments
  action({ commit, state, dispatch }, payload)

  // check if no mutations should have been dispatched
  if (expectedMutations.length === 0) {
    expect(count).to.equal(0)
    done()
  }
}
